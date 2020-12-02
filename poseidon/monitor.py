#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import queue
import random
import re
import sys
import threading
import time
from functools import partial

import requests
import schedule

from poseidon.helpers.actions import Actions
from poseidon.helpers.config import Config
from poseidon.helpers.prometheus import Prometheus
from poseidon.sdnconnect import SDNConnect

requests.packages.urllib3.disable_warnings()


class Monitor:

    def __init__(self, logger, controller=None):
        self.logger = logger
        self.m_queue = queue.Queue()
        self.job_queue = queue.Queue()
        self.rabbits = []
        self.running = True

        # get config options
        if controller is None:
            self.controller = Config().get_config()
        else:
            self.controller = controller

        # setup prometheus
        self.prom = Prometheus()
        try:
            self.prom.initialize_metrics()
        except Exception as e:  # pragma: no cover
            self.logger.debug(
                'Prometheus metrics are already initialized: {0}'.format(str(e)))
        Prometheus.start()

        # initialize sdnconnect
        self.s = SDNConnect(self.controller, self.logger)
        self.s.default_endpoints()

        # timer class to call things periodically in own thread
        self.schedule = schedule
        self.schedule.every(self.controller['scan_frequency']).seconds.do(
            self.schedule_job_update_metrics)
        self.schedule.every(self.controller['reinvestigation_frequency']).seconds.do(
            self.schedule_job_reinvestigation)

        # schedule all threads
        self.schedule_thread = threading.Thread(
            target=partial(
                self.schedule_thread_worker,
                scheduler=self.schedule),
            name='st_worker')

    def schedule_thread_worker(self, scheduler=schedule):
        ''' schedule thread, takes care of running processes in the future '''
        self.logger.debug('Starting thread_worker')
        while self.running:
            sys.stdout.flush()
            scheduler.run_pending()
            time.sleep(1)

    def rabbit_callback(self, ch, method, _properties, body, q=None):
        ''' callback, places rabbit data into internal queue'''
        self.logger.debug('got a message: {0}:{1}:{2} (qsize {3})'.format(
            method.routing_key, body, type(body), q.qsize()))
        if q is not None:
            q.put((method.routing_key, body))
        else:
            self.logger.debug('poseidonMain workQueue is None')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def job_update_metrics(self):
        self.logger.debug('updating metrics')
        try:
            # get current state
            req = requests.get(
                'http://poseidon-api:8000/v1/network_full', timeout=10)
            # send results to prometheus
            hosts = req.json()['dataset']
            self.prom.update_metrics(hosts)
        except (requests.exceptions.ConnectionError, Exception) as e:  # pragma: no cover
            self.logger.error(
                'Unable to get current state and send it to Prometheus because: {0}'.format(str(e)))
        return 0

    def job_recoprocess(self):
        if not self.s.sdnc:
            for endpoint in self.s.not_copro_ignored_endpoints():
                if endpoint.copro_state != 'copro_nominal':
                    endpoint.copro_nominal()  # pytype: disable=attribute-error
            return 0
        events = 0
        for endpoint in self.s.not_copro_ignored_endpoints():
            if endpoint.copro_state == 'copro_coprocessing':
                if endpoint.copro_state_timeout(2*self.controller['coprocessing_frequency']):
                    self.logger.debug(
                        'timing out: {0} and setting to unknown'.format(endpoint.name))
                    self.s.uncoprocess_endpoint(endpoint)
                    endpoint.copro_unknown()  # pytype: disable=attribute-error
                    events += 1
        return events

    def job_reinvestigation(self):
        ''' put endpoints into the reinvestigation state if possible, and timeout investigations '''
        if not self.s.sdnc:
            for endpoint in self.s.not_ignored_endpoints():
                if endpoint.state != 'known':
                    endpoint.known()  # pytype: disable=attribute-error
            return 0
        events = 0
        for endpoint in self.s.not_ignored_endpoints():
            if endpoint.mirror_active():
                if endpoint.state_timeout(2*self.controller['reinvestigation_frequency']):
                    self.logger.debug(
                        'timing out: {0} and setting to unknown'.format(endpoint.name))
                    self.s.unmirror_endpoint(endpoint)
                    events += 1
        budget = self.s.investigation_budget()
        candidates = self.s.not_ignored_endpoints('queued')
        if not candidates:
            candidates = self.s.not_ignored_endpoints('known')
        return events + self._schedule_queued_work(
            candidates, budget, 'reinvestigate', self.s.mirror_endpoint, shuffle=True)

    def queue_job(self, job):
        if self.job_queue.qsize() < 2:
            self.job_queue.put(job)

    def schedule_job_update_metrics(self):
        self.queue_job(self.job_update_metrics)

    def schedule_job_reinvestigation(self):
        self.queue_job(self.job_reinvestigation)

    def update_routing_key_time(self, routing_key):
        self.prom.prom_metrics['last_rabbitmq_routing_key_time'].labels(
            routing_key=routing_key).set(time.time())

    def format_rabbit_message(self, item, faucet_event, remove_list):
        '''
        read a message off the rabbit_q
        the message should be item = (routing_key,msg)
        '''
        routing_key, my_obj = item
        self.logger.debug(
            'routing_key: {0} rabbit_message: {1}'.format(routing_key, my_obj))
        my_obj = json.loads(my_obj)

        def handler_algos_decider(my_obj):
            self.logger.debug('decider value:{0}'.format(my_obj))
            data = my_obj.get('data', None)
            results = my_obj.get('results', {})
            tool = results.get('tool', None)
            if isinstance(data, dict):
                if tool == 'p0f':
                    if self.s.prc.store_p0f_result(data):
                        return data
                elif tool == 'networkml':
                    self.s.prc.store_tool_result(my_obj, 'networkml')
                    for name, message in data.items():
                        endpoint = self.s.endpoints.get(name, None)
                        if endpoint:
                            self.logger.debug(
                                'processing networkml results for %s', name)
                            self.s.unmirror_endpoint(endpoint)
                            if message.get('valid', False):
                                return data
                            break
                        else:
                            self.logger.debug(
                                'endpoint %s from networkml not found', name)
            return {}

        def handler_action_ignore(my_obj):
            for name in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = True
            return {}

        def handler_action_clear_ignored(my_obj):
            for name in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = False
            return {}

        def handler_action_change(my_obj):
            for name, state in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    try:
                        if endpoint.mirror_active():
                            self.s.unmirror_endpoint(endpoint)
                        endpoint.machine_trigger(state)  # pytype: disable=attribute-error
                        endpoint.p_next_state = None
                        if endpoint.mirror_active():
                            self.s.mirror_endpoint(endpoint)
                            self.prom.prom_metrics['ncapture_count'].inc()
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to change endpoint {0} because: {1}'.format(endpoint.name, str(e)))
            return {}

        def handler_action_update_acls(my_obj):
            for ip in my_obj:
                rules = my_obj[ip]
                endpoints = self.s.endpoints_by_ip(ip)
                if endpoints:
                    endpoint = endpoints[0]
                    try:
                        status = Actions(
                            endpoint, self.s.sdnc).update_acls(
                                rules_file=self.controller['RULES_FILE'], endpoints=endpoints, force_apply_rules=rules)
                        if not status:
                            self.logger.warning(
                                'Unable to apply rules: {0} to endpoint: {1}'.format(rules, endpoint.name))
                    except Exception as e:
                        self.logger.error(
                            'Unable to apply rules: {0} to endpoint: {1} because {2}'.format(rules, endpoint.name, str(e)))
            return {}

        def handler_action_remove(my_obj):
            remove_list.extend([name for name in my_obj])
            return {}

        def handler_action_remove_ignored(_my_obj):
            remove_list.extend([
                endpoint.name for endpoint in self.s.endpoints.values()
                if endpoint.ignore])
            return {}

        def handler_action_remove_inactives(_my_obj):
            remove_list.extend([
                endpoint.name for endpoint in self.s.endpoints.values()
                if endpoint.state == 'inactive'])
            return {}

        def handler_faucet_event(my_obj):
            if self.s and self.s.sdnc:
                if not self.s.sdnc.ignore_event(my_obj):
                    faucet_event.append(my_obj)
                    return my_obj
            return {}

        handlers = {
            'poseidon.algos.decider': handler_algos_decider,
            'poseidon.action.ignore': handler_action_ignore,
            'poseidon.action.clear.ignored': handler_action_clear_ignored,
            'poseidon.action.change': handler_action_change,
            'poseidon.action.update_acls': handler_action_update_acls,
            'poseidon.action.remove': handler_action_remove,
            'poseidon.action.remove.ignored': handler_action_remove_ignored,
            'poseidon.action.remove.inactives': handler_action_remove_inactives,
            self.controller['FA_RABBIT_ROUTING_KEY']: handler_faucet_event,
        }

        handler = handlers.get(routing_key, None)
        if handler is not None:
            ret_val = handler(my_obj)
            self.update_routing_key_time(routing_key)
            return ret_val, True

        self.logger.error(
            'no handler for routing_key {0}'.format(routing_key))
        return {}, False

    def _schedule_queued_work(self, queued_endpoints, budget, endpoint_state, endpoint_work, shuffle=False):
        events = 0
        if self.s.sdnc:
            if shuffle:
                random.shuffle(queued_endpoints)
            for endpoint in queued_endpoints[:budget]:
                getattr(endpoint, endpoint_state)()
                endpoint_work(endpoint)
                if endpoint_state in ['trigger_next', 'reinvestigate']:
                    self.prom.prom_metrics['ncapture_count'].inc()
                events += 1
        return events

    def schedule_mirroring(self):
        for endpoint in self.s.not_ignored_endpoints('unknown'):
            endpoint.queue_next('mirror')
        budget = self.s.investigation_budget()
        queued_endpoints = [
            endpoint for endpoint in self.s.not_ignored_endpoints('queued')
            if endpoint.mirror_requested()]
        queued_endpoints = sorted(queued_endpoints, key=lambda x: x.state_time())
        self.logger.debug('investigations {0}, budget {1}, queued {2}'.format(
            str(self.s.investigations), str(budget), str(len(queued_endpoints))))
        return self._schedule_queued_work(queued_endpoints, budget, 'trigger_next', self.s.mirror_endpoint)

    def schedule_coprocessing(self):
        for endpoint in self.s.not_copro_ignored_endpoints('copro_unknown'):
            endpoint.copro_queue_next('copro_coprocess')
        budget = self.s.coprocessing_budget()
        queued_endpoints = self.s.not_copro_ignored_endpoints('copro_queued')
        queued_endpoints = sorted(queued_endpoints, key=lambda x: x.copro_state_time())
        self.logger.debug('coprocessing {0}, budget {1}, queued {2}'.format(
            str(self.s.coprocessing), str(budget), str(len(queued_endpoints))))
        return self._schedule_queued_work(queued_endpoints, budget, 'copro_trigger_next', self.s.coprocess_endpoint)

    def monitor_callable(self, monitored_callable):
        method_name = str(monitored_callable)
        method_re = re.compile(r'.+bound method (\S+).+')
        method_match = method_re.match(method_name)
        if method_match:
            method_name = method_match.group(1)
        with self.prom.prom_metrics['monitor_runtime_secs'].labels(method=method_name).time():
            return monitored_callable()

    def handle_rabbit(self):
        events = 0
        faucet_event = []
        remove_list = []
        while True:
            found_work, rabbit_msg = self.monitor_callable(partial(self.get_q_item, self.m_queue))
            if not found_work:
                break
            events += 1
            self.monitor_callable(partial(self.format_rabbit_message, rabbit_msg, faucet_event, remove_list))
        return (events, faucet_event, remove_list)

    def process(self):
        while self.running:
            events, faucet_event, remove_list = self.monitor_callable(self.handle_rabbit)
            if remove_list:
                for endpoint_name in remove_list:
                    if endpoint_name in self.s.endpoints:
                        del self.s.endpoints[endpoint_name]
            if faucet_event:
                self.monitor_callable(partial(self.s.check_endpoints, faucet_event))
            events += self.monitor_callable(self.schedule_mirroring)
            found_work, schedule_func = self.monitor_callable(partial(self.get_q_item, self.job_queue))
            if found_work and callable(schedule_func):
                events += self.monitor_callable(schedule_func)
            if events:
                self.monitor_callable(self.s.refresh_endpoints)
            else:
                time.sleep(1)

    @staticmethod
    def get_q_item(q):
        '''
        attempt to get a work item from the queue
        m_queue -> (routing_key, body)
        a read from get_q_item should be of the form
        (boolean,(routing_key, body))
        '''
        try:
            return (True, q.get_nowait())
        except queue.Empty:  # pragma: no cover
            pass

        return (False, None)
