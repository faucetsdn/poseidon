#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import queue
import random
import signal
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

    def __init__(self, logger, ctrl_c, controller=None):
        self.logger = logger
        self.ctrl_c = ctrl_c
        self.m_queue = queue.Queue()
        self.job_queue = queue.Queue()
        self.rabbits = []

        # get config options
        if controller is None:
            self.controller = Config().get_config()
        else:
            self.controller = controller

        # timer class to call things periodically in own thread
        self.schedule = schedule

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

        # schedule periodic scan of endpoints thread
        self.schedule.every(self.controller['scan_frequency']).seconds.do(
            self.schedule_job_kickurl)

        # schedule periodic reinvestigations thread
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
        while not self.ctrl_c['STOP']:
            sys.stdout.flush()
            scheduler.run_pending()
            time.sleep(1)
        self.logger.debug('Threading stop:{0}'.format(
            threading.current_thread().getName()))

    def rabbit_callback(self, ch, method, _properties, body, q=None):
        ''' callback, places rabbit data into internal queue'''
        self.logger.debug('got a message: {0}:{1}:{2} (qsize {3})'.format(
            method.routing_key, body, type(body), q.qsize()))
        if q is not None:
            q.put((method.routing_key, body))
        else:
            self.logger.debug('poseidonMain workQueue is None')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _update_metrics(self):
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

    def job_kickurl(self):
        self._update_metrics()

    def job_reinvestigation(self):
        ''' put endpoints into the reinvestigation state if possible '''

        def trigger_reinvestigation(candidates):
            # get random order of things that are known
            for _ in range(self.controller['max_concurrent_reinvestigations'] - self.s.investigations):
                if len(candidates) > 0:
                    chosen = candidates.pop()
                    self.logger.info('Starting reinvestigation on: {0} {1}'.format(
                        chosen.name, chosen.state))
                    chosen.reinvestigate()  # pytype: disable=attribute-error
                    self.s.mirror_endpoint(chosen)

        candidates = [
            endpoint for endpoint in self.s.endpoints.values()
            if endpoint.state in ['queued']]
        if len(candidates) == 0:
            # if no queued endpoints, then known and abnormal are candidates
            candidates = [
                endpoint for endpoint in self.s.endpoints.values()
                if endpoint.state in ['known', 'abnormal']]
            if len(candidates) > 0:
                random.shuffle(candidates)
        if self.s.sdnc:
            trigger_reinvestigation(candidates)

    def queue_job(self, job):
        if self.job_queue.qsize() < 2:
            self.job_queue.put(job)

    def schedule_job_kickurl(self):
        self.queue_job(self.job_kickurl)

    def schedule_job_reinvestigation(self):
        self.queue_job(self.job_reinvestigation)

    def update_routing_key_time(self, routing_key):
        self.prom.prom_metrics['last_rabbitmq_routing_key_time'].labels(
            routing_key=routing_key).set(time.time())

    def _unmirror_endpoint(self, endpoint):
        if endpoint.mirror_active():
            self.s.unmirror_endpoint(endpoint)
            endpoint.unknown()
            endpoint.p_next_state = None

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
                            self._unmirror_endpoint(endpoint)
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
                            self._unmirror_endpoint(endpoint)
                        # pytype: disable=attribute-error
                        endpoint.trigger(state)
                        endpoint.p_next_state = None
                        if endpoint.mirror_active():
                            self.s.mirror_endpoint(endpoint)
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

    def _not_ignored_endpoints(self):
        return [endpoint for endpoint in self.s.endpoints.values() if not endpoint.ignore]

    def schedule_mirroring(self):
        queued_endpoints = [
            endpoint for endpoint in self._not_ignored_endpoints()
            if endpoint.state == 'queued' and endpoint.mirror_requested()]
        self.s.investigations = len([
            endpoint for endpoint in self._not_ignored_endpoints()
            if endpoint.mirror_active()])
        # mirror things in the order they got added to the queue
        queued_endpoints = sorted(
            queued_endpoints, key=lambda x: x.state_time())

        investigation_budget = max(
            self.controller['max_concurrent_reinvestigations'] -
            self.s.investigations,
            0)
        self.logger.debug('investigations {0}, budget {1}, queued {2}'.format(
            str(self.s.investigations), str(investigation_budget), str(len(queued_endpoints))))

        for endpoint in queued_endpoints[:investigation_budget]:
            # pytype: disable=attribute-error
            endpoint.trigger_next()
            self.s.mirror_endpoint(endpoint)

        for endpoint in self._not_ignored_endpoints():
            if self.s.sdnc:
                if endpoint.state == 'unknown':
                    endpoint.queue_next('mirror')
                elif endpoint.mirror_active():
                    # timeout after 2 times the reinvestigation frequency
                    # in case something didn't report back, put back in an
                    # unknown state
                    if endpoint.state_age() > 2*self.controller['reinvestigation_frequency']:
                        self.logger.debug(
                            'timing out: {0} and setting to unknown'.format(endpoint.name))
                        self._unmirror_endpoint(endpoint)
            else:
                if endpoint.state != 'known':
                    endpoint.known()  # pytype: disable=attribute-error

    def schedule_coprocessing(self):
        queued_endpoints = [
            endpoint for endpoint in self.s.endpoints.values()
            if not endpoint.copro_ignore and endpoint.copro_state == 'copro_queued']  # pytype: disable=attribute-error
        self.s.coprocessing = len([
            endpoint for endpoint in self.s.endpoints.values()
            if endpoint.copro_state in ['copro_coprocessing']])
        # mirror things in the order they got added to the queue
        queued_endpoints = sorted(
            queued_endpoints, key=lambda x: x.p_prev_copro_states[-1][1])

        coprocessing_budget = max(
            self.controller['max_concurrent_coprocessing'] -
            self.s.coprocessing,
            0)
        self.logger.debug('coprocessing {0}, budget {1}, queued {2}'.format(
            str(self.s.coprocessing), str(coprocessing_budget), str(len(queued_endpoints))))

        for endpoint in queued_endpoints[:coprocessing_budget]:
            # pytype: disable=attribute-error
            endpoint.trigger(endpoint.p_next_copro_state)
            endpoint.p_next_copro_state = None  # pytype: disable=attribute-error
            endpoint.p_prev_copro_states.append(  # pytype: disable=attribute-error
                (endpoint.copro_state, int(time.time())))
            self.s.coprocess_endpoint(endpoint)

        for endpoint in self.s.endpoints.values():
            if not endpoint.copro_ignore:  # pytype: disable=attribute-error
                if self.s.sdnc:
                    if endpoint.copro_state == 'copro_unknown':  # pytype: disable=attribute-error
                        endpoint.p_next_copro_state = 'copro_coprocessing'
                        endpoint.copro_queue()  # pytype: disable=attribute-error
                        endpoint.p_prev_copro_states.append(  # pytype: disable=attribute-error
                            (endpoint.copro_state, int(time.time())))
                    # pytype: disable=attribute-error
                    elif endpoint.copro_state in ['copro_coprocessing']:
                        cur_time = int(time.time())
                        # timeout after 2 times the reinvestigation frequency
                        # in case something didn't report back, put back in an
                        # unknown state
                        # pytype: disable=attribute-error
                        if cur_time - endpoint.p_prev_copro_states[-1][1] > 2*self.controller['coprocessing_frequency']:
                            self.logger.debug(
                                'timing out: {0} and setting to unknown'.format(endpoint.name))
                            self.s.uncoprocess_endpoint(endpoint)
                            endpoint.copro_unknown()  # pytype: disable=attribute-error
                            endpoint.p_prev_copro_states.append(  # pytype: disable=attribute-error
                                (endpoint.copro_state, int(time.time())))  # pytype: disable=attribute-error
                else:
                    if endpoint.state != 'copro_nominal':
                        endpoint.copro_nominal()  # pytype: disable=attribute-error

    def process(self):
        signal.signal(signal.SIGINT, partial(self.signal_handler))
        while not self.ctrl_c['STOP']:
            faucet_event = []
            remove_list = []
            while True:
                found_work, rabbit_msg = self.get_q_item(self.m_queue)
                if not found_work:
                    break
                self.format_rabbit_message(rabbit_msg, faucet_event, remove_list)
            if remove_list:
                for endpoint_name in remove_list:
                    if endpoint_name in self.s.endpoints:
                        del self.s.endpoints[endpoint_name]
            self.s.refresh_endpoints()
            if faucet_event:
                self.s.check_endpoints(faucet_event)
            found_work, schedule_func = self.get_q_item(self.job_queue)
            if found_work and callable(schedule_func):
                self.logger.info('calling %s', schedule_func)
                start_time = time.time()
                schedule_func()
                self.logger.debug('%s done (%.1f sec)' % (schedule_func, time.time() - start_time))
            self.schedule_mirroring()

    def get_q_item(self, q, timeout=1):
        '''
        attempt to get a work item from the queue
        m_queue -> (routing_key, body)
        a read from get_q_item should be of the form
        (boolean,(routing_key, body))
        '''
        if not self.ctrl_c['STOP']:
            try:
                if timeout:
                    return(True, q.get(True, timeout=timeout))
                return (True, q.get_nowait())
            except queue.Empty:  # pragma: no cover
                pass

        return (False, None)

    def shutdown(self):
        ''' gracefully shut down. '''
        self.s.clear_filters()
        self.s.refresh_endpoints()
        for job in self.schedule.jobs:
            self.logger.debug('shutdown :{0}'.format(job))
            self.schedule.cancel_job(job)
        for rabbit in self.rabbits:
            rabbit.close()
        self.logger.debug('SHUTTING DOWN')
        self.logger.debug('EXITING')

    def signal_handler(self, _signal, _frame, sig_exit=True):
        ''' hopefully eat a CTRL_C and signal system shutdown '''
        self.ctrl_c['STOP'] = True
        self.logger.debug('CTRL-C: {0}'.format(self.ctrl_c))
        try:
            self.shutdown()
        except Exception as e:  # pragma: no cover
            self.logger.debug(
                'Failed to handle signal properly because: {0}'.format(str(e)))
        if sig_exit:
            sys.exit(0)
