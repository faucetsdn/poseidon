#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import queue
import random
import re
import sys
import threading
import time
from collections import defaultdict
from functools import partial

import requests
import schedule

from poseidon_core.helpers.actions import Actions
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.prometheus import Prometheus
from poseidon_core.sdnconnect import SDNConnect

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
        self.update_endpoint_metadata()

        # timer class to call things periodically in own thread
        self.schedule = schedule
        self.schedule.every(self.controller['scan_frequency']).seconds.do(
            self.schedule_job_update_metrics)
        self.schedule.every(self.controller['reinvestigation_frequency']).seconds.do(
            self.schedule_job_reinvestigation_timeout)

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

    def get_hosts(self):
        # TODO consolidate with update_endpoint_metadata
        hosts = []
        for hash_id, endpoint in self.s.endpoints.items():
            roles, _, _ = endpoint.get_roles_confidences_pcap_labels()
            role = roles[0]
            ipv4_os = endpoint.get_ipv4_os()
            host = {
                'mac': endpoint.endpoint_data['mac'],
                'id': hash_id,
                'role': role,
                'ipv4_os': ipv4_os,
                'state': endpoint.state,
                'tenant': endpoint.endpoint_data['tenant'],
                'port': endpoint.endpoint_data['port'],
                'segment': endpoint.endpoint_data['segment'],
                'ipv4': endpoint.endpoint_data['ipv4']}
            hosts.append(host)
        return hosts

    def job_update_metrics(self):
        self.logger.debug('updating metrics')
        try:
            hosts = self.get_hosts()
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
        for endpoint in self.s.not_copro_ignored_endpoints('copro_coprocessing'):
            if endpoint.copro_state_timeout(2*self.controller['coprocessing_frequency']):
                self.logger.debug(
                    'timing out: {0} and setting to unknown'.format(endpoint.name))
                self.s.uncoprocess_endpoint(endpoint)
                endpoint.copro_unknown()  # pytype: disable=attribute-error
                events += 1
        return events

    def job_reinvestigation_timeout(self):
        ''' put endpoints into the reinvestigation state if possible, and timeout investigations '''
        if not self.s.sdnc:
            for endpoint in self.s.not_ignored_endpoints():
                if endpoint.state != 'known':
                    endpoint.known()  # pytype: disable=attribute-error
            return 0
        events = 0
        timeout = 2*self.controller['reinvestigation_frequency']
        for endpoint in self.s.not_ignored_endpoints():
            if endpoint.observed_timeout(timeout):
                self.logger.info('observation timing out: {0}'.format(endpoint.name))
                endpoint.force_unknown()
                events += 1
            elif endpoint.mirror_active() and endpoint.state_timeout(timeout):
                self.logger.info('mirror timing out: {0}'.format(endpoint.name))
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

    def schedule_job_reinvestigation_timeout(self):
        self.queue_job(self.job_reinvestigation_timeout)

    def update_routing_key_time(self, routing_key):
        self.prom.prom_metrics['last_rabbitmq_routing_key_time'].labels(
            routing_key=routing_key).set(time.time())

    def update_endpoint_metadata(self):
        update_time = time.time()
        for hash_id, endpoint in self.s.endpoints.items():
            ipv4 = endpoint.endpoint_data['ipv4']
            ipv6 = endpoint.endpoint_data['ipv6']
            ipv4_subnet = endpoint.endpoint_data['ipv4_subnet']
            ipv6_subnet = endpoint.endpoint_data['ipv6_subnet']
            ipv4_rdns = endpoint.endpoint_data['ipv4_rdns']
            ipv6_rdns = endpoint.endpoint_data['ipv6_rdns']
            port = endpoint.endpoint_data['port']
            tenant = endpoint.endpoint_data['tenant']
            segment = endpoint.endpoint_data['segment']
            ether_vendor = endpoint.endpoint_data['ether_vendor']
            controller = endpoint.endpoint_data['controller']
            controller_type = endpoint.endpoint_data['controller_type']
            roles, confidences, pcap_labels = endpoint.get_roles_confidences_pcap_labels()
            top_role, second_role, third_role = roles
            top_conf, second_conf, third_conf = confidences
            ipv4_os = endpoint.get_ipv4_os()

            def set_prom(var, val, **prom_labels):
                prom_labels.update({
                    'mac': endpoint.endpoint_data['mac'],
                    'name': endpoint.endpoint_data['name'],
                    'hash_id': hash_id,
                })
                try:
                    self.prom.prom_metrics[var].labels(**prom_labels).set(val)
                except ValueError:
                    pass

            def set_prom_role(var, val, role):
                set_prom(
                    var,
                    val,
                    role=role,
                    ipv4_os=ipv4_os,
                    ipv4_address=ipv4,
                    ipv6_address=ipv6,
                    pcap_labels=pcap_labels)

            def update_prom(var, **prom_labels):
                prom_labels.update({
                    'tenant': tenant,
                    'segment': segment,
                    'ether_vendor': ether_vendor,
                    'port': port,
                })
                set_prom(var, update_time, **prom_labels)

            set_prom_role(
                'endpoint_role_confidence_top',
                top_conf,
                top_role)
            set_prom_role(
                'endpoint_role_confidence_second',
                second_conf,
                second_role)
            set_prom_role(
                'endpoint_role_confidence_third',
                third_conf,
                third_role)
            update_prom(
                'endpoints',
                controller_type=controller_type,
                controller=controller)
            update_prom(
                'endpoint_state',
                state=endpoint.state)
            update_prom(
                'endpoint_os',
                ipv4_os=ipv4_os)
            update_prom(
                'endpoint_role',
                top_role=top_role)
            update_prom(
                'endpoint_ip',
                ipv4_subnet=ipv4_subnet,
                ipv6_subnet=ipv6_subnet,
                ipv4_rdns=ipv4_rdns,
                ipv6_rdns=ipv6_rdns,
                ipv4_address=ipv4,
                ipv6_address=ipv6)
            update_prom(
                'endpoint_metadata',
                prev_state=endpoint.p_prev_state,
                next_state=endpoint.p_next_state,
                acls=endpoint.acl_data,
                ignore=str(endpoint.ignore),
                ipv4_subnet=ipv4_subnet,
                ipv6_subnet=ipv6_subnet,
                ipv4_rdns=ipv4_rdns,
                ipv6_rdns=ipv6_rdns,
                controller_type=controller_type,
                controller=controller,
                state=endpoint.state,
                top_role=top_role,
                ipv4_os=ipv4_os,
                ipv4_address=ipv4,
                ipv6_address=ipv6)

    def merge_metadata(self, new_metadata):
        updated = set()
        metadata_types = {
            'mac_addresses': self.s.endpoints_by_mac,
            'ipv4_addresses': self.s.endpoints_by_ip,
            'ipv6_addresses': self.s.endpoints_by_ip,
        }
        for metadata_type, metadata_lookup in metadata_types.items():
            type_new_metadata = new_metadata.get(metadata_type, {})
            for key, data in type_new_metadata.items():
                endpoints = metadata_lookup(key)
                if endpoints:
                    endpoint = endpoints[0]
                    if metadata_type not in endpoint.metadata:
                        endpoint.metadata[metadata_type] = defaultdict(dict)
                    endpoint.metadata[metadata_type][key].update(data)
                    updated.add(endpoint)
        return updated

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
            if isinstance(data, dict) and data:
                new_metadata = data
                if tool == 'p0f':
                    ip_metadata = {}
                    for ip, ip_data in data.items():
                        if ip_data and ip_data.get('full_os', None):
                            ip_metadata[ip] = ip_data
                    new_metadata = {'ipv4_addresses': ip_metadata}
                elif tool == 'networkml':
                    mac_metadata = {}
                    for name, message in data.items():
                        if name == 'pcap':
                            continue
                        if message.get('valid', False):
                            source_mac = message.get('source_mac', None)
                            if source_mac:
                                mac_metadata[source_mac] = message
                    new_metadata = {'mac_addresses': mac_metadata}
                # Generic handler for future tools.
                updated = self.merge_metadata(new_metadata)
                if updated:
                    for endpoint in updated:
                        if endpoint.mirror_active():
                            self.s.unmirror_endpoint(endpoint)
                    self.job_update_metrics()
                    return data
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
        queued_endpoints = sorted(queued_endpoints, key=lambda x: x.state_time)
        self.logger.debug('investigations {0}, budget {1}, queued {2}'.format(
            str(self.s.investigations), str(budget), str(len(queued_endpoints))))
        return self._schedule_queued_work(queued_endpoints, budget, 'trigger_next', self.s.mirror_endpoint)

    def schedule_coprocessing(self):
        for endpoint in self.s.not_copro_ignored_endpoints('copro_unknown'):
            endpoint.copro_queue_next('copro_coprocess')
        budget = self.s.coprocessing_budget()
        queued_endpoints = self.s.not_copro_ignored_endpoints('copro_queued')
        queued_endpoints = sorted(queued_endpoints, key=lambda x: x.copro_state_time)
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
            # faucet_event and remove_list get updated as references because partial()
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
                self.monitor_callable(self.update_endpoint_metadata)
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
            item = q.get_nowait()
            q.task_done()
            return (True, item)
        except queue.Empty:  # pragma: no cover
            pass

        return (False, None)
