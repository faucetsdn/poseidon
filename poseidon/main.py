#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon, schedules the threads, connects to SDN
controllers and defines the Monitor class.

Created on 3 December 2018
@author: Charlie Lewis
"""
import difflib
import ipaddress
import json
import logging
import queue
import random
import signal
import sys
import threading
import time
from copy import deepcopy
from functools import partial

import pika
import requests
import schedule


from poseidon.constants import NO_DATA
from poseidon.controllers.bcf.bcf import BcfProxy
from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.controllers.faucet.parser import Parser
from poseidon.helpers.actions import Actions
from poseidon.helpers.config import Config
from poseidon.helpers.endpoint import Endpoint
from poseidon.helpers.endpoint import MACHINE_IP_FIELDS
from poseidon.helpers.endpoint import MACHINE_IP_PREFIXES
from poseidon.helpers.endpoint import endpoint_factory
from poseidon.helpers.log import Logger
from poseidon.helpers.metadata import get_ether_vendor
from poseidon.helpers.metadata import get_rdns_lookup
from poseidon.helpers.prometheus import Prometheus
from poseidon.helpers.rabbit import Rabbit
from poseidon.helpers.redis import PoseidonRedisClient

requests.packages.urllib3.disable_warnings()
logging.getLogger('pika').setLevel(logging.WARNING)

CTRL_C = dict()
CTRL_C['STOP'] = False
Logger()
logger = logging.getLogger('main')



def rabbit_callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    if q is not None:
        q.put((method.routing_key, body))
    else:
        logger.debug('poseidonMain workQueue is None')
    ch.basic_ack(delivery_tag=method.delivery_tag)


def schedule_job_coprocessing(schedule_func):
    ''' put endpoints into the reinvestigation state if possible '''
    global CTRL_C

    def trigger_coprocessing(candidates):
        # get random order of things that are known
        for _ in range(schedule_func.controller['max_concurrent_coprocessing'] - schedule_func.s.coprocessing):
            if len(candidates) > 0:
                chosen = candidates.pop()
                schedule_func.logger.info('Starting coprocessing on: {0} {1}'.format(
                    chosen.name, chosen.state))
                chosen.copro_coprocess()
                chosen.p_prev_states.append(
                    (chosen.state, int(time.time())))
                schedule_func.s.coprocess_endpoint(chosen)

    if not CTRL_C['STOP'] and schedule_func.s.volos.enabled:
        if schedule_func.s.coprocessor and not schedule_func.s.coprocessor.pipette_running:
            schedule_func.s.start_pipette
            schedule_func.s.pipette_running = True

        candidates = [
            endpoint for endpoint in schedule_func.s.endpoints.values()
            if endpoint.state in ['queued']]
        if len(candidates) == 0:
            # if no queued endpoints, then known and abnormal are candidates
            candidates = [
                endpoint for endpoint in schedule_func.s.endpoints.values()
                if endpoint.state in ['known', 'abnormal']]
            if len(candidates) > 0:
                random.shuffle(candidates)
        if schedule_func.s.sdnc:
            trigger_coprocessing(candidates)
    else:
        if schedule_func.s.coprocessor and schedule_func.s.coprocessor.pipette_running:
            schedule_func.s.stop_pipette
            schedule_func.s.pipette_running = False


def schedule_thread_worker(schedule):
    ''' schedule thread, takes care of running processes in the future '''
    global CTRL_C
    logger.debug('Starting thread_worker')
    while not CTRL_C['STOP']:
        sys.stdout.flush()
        schedule.run_pending()
        time.sleep(1)
    logger.debug('Threading stop:{0}'.format(
        threading.current_thread().getName()))
    sys.exit()


class SDNConnect:

    def __init__(self, controller, first_time=True):
        self.controller = controller
        self.r = None
        self.first_time = first_time
        self.sdnc = None
        self.endpoints = {}
        trunk_ports = self.controller['trunk_ports']
        if isinstance(trunk_ports, str):
            self.trunk_ports = json.loads(trunk_ports)
        else:
            self.trunk_ports = trunk_ports
        self.logger = logger
        self.get_sdn_context()
        self.prc = PoseidonRedisClient(self.logger)
        self.prc.connect()
        if self.first_time:
            self.endpoints = {}
            self.investigations = 0
            self.coprocessing = 0
            self.clear_filters()
            self.default_endpoints()

    def mirror_endpoint(self, endpoint):
        ''' mirror an endpoint. '''
        status = Actions(endpoint, self.sdnc).mirror_endpoint()
        if status:
            self.prc.inc_network_tools_counts()
        else:
            self.logger.warning(
                'Unable to mirror the endpoint: {0}'.format(endpoint.name))

    def unmirror_endpoint(self, endpoint):
        ''' unmirror an endpoint. '''
        status = Actions(endpoint, self.sdnc).unmirror_endpoint()
        if not status:
            self.logger.warning(
                'Unable to unmirror the endpoint: {0}'.format(endpoint.name))

    def clear_filters(self):
        ''' clear any exisiting filters. '''
        if isinstance(self.sdnc, FaucetProxy):
            Parser().clear_mirrors(self.controller['CONFIG_FILE'])
        elif isinstance(self.sdnc, BcfProxy):
            self.logger.debug('removing bcf filter rules')
            retval = self.sdnc.remove_filter_rules()
            self.logger.debug('removed filter rules: {0}'.format(retval))

    def default_endpoints(self):
        ''' set endpoints to default state. '''
        self.get_stored_endpoints()
        for endpoint in self.endpoints.values():
            if not endpoint.ignore:
                if endpoint.state != 'inactive':
                    if endpoint.state == 'mirroring':
                        endpoint.p_next_state = 'mirror'
                    elif endpoint.state == 'reinvestigating':
                        endpoint.p_next_state = 'reinvestigate'
                    elif endpoint.state == 'queued':
                        endpoint.p_next_state = 'queue'
                    elif endpoint.state in ['known', 'abnormal']:
                        endpoint.p_next_state = endpoint.state
                    endpoint.endpoint_data['active'] = 0
                    endpoint.inactive()  # pytype: disable=attribute-error
                    endpoint.p_prev_states.append(
                        (endpoint.state, int(time.time())))
        self.store_endpoints()

    def get_stored_endpoints(self):
        ''' load existing endpoints from Redis. '''
        new_endpoints = self.prc.get_stored_endpoints()
        if new_endpoints:
            self.endpoints = new_endpoints

    def get_sdn_context(self):
        controller_type = self.controller.get('TYPE', None)
        if controller_type == 'bcf':
            try:
                self.sdnc = BcfProxy(self.controller)
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'BcfProxy could not connect to {0} because {1}'.format(
                        self.controller['URI'], e))
        elif controller_type == 'faucet':
            try:
                self.sdnc = FaucetProxy(self.controller)
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'FaucetProxy could not connect to {0} because {1}'.format(
                        self.controller['URI'], e))
        elif controller_type == 'None':
            self.sdnc = None
        else:
            if 'CONTROLLER_PASS' in self.controller:
                self.controller['CONTROLLER_PASS'] = '********'
            self.logger.error(
                'Unknown SDN controller config: {0}'.format(
                    self.controller))

    def endpoint_by_name(self, name):
        return self.endpoints.get(name, None)

    def endpoint_by_hash(self, hash_id):
        return self.endpoint_by_name(hash_id)

    def endpoints_by_ip(self, ip):
        endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if ip == endpoint.endpoint_data.get('ipv4', None) or
            ip == endpoint.endpoint_data.get('ipv6', None)]
        return endpoints

    def endpoints_by_mac(self, mac):
        endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if mac == endpoint.endpoint_data['mac']]
        return endpoints

    @staticmethod
    def _connect_rabbit():
        # Rabbit settings
        exchange = 'topic-poseidon-internal'
        exchange_type = 'topic'

        # Starting rabbit connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='RABBIT_SERVER')
        )

        channel = connection.channel()
        channel.exchange_declare(
            exchange=exchange, exchange_type=exchange_type
        )

        return channel, exchange, connection

    @staticmethod
    def publish_action(action, message):
        try:
            channel, exchange, connection = SDNConnect._connect_rabbit()
            channel.basic_publish(exchange=exchange,
                                  routing_key=action,
                                  body=message)
            connection.close()
        except Exception as e:  # pragma: no cover
            print(str(e))

    def show_endpoints(self, arg):
        endpoints = []
        if arg == 'all':
            endpoints = list(self.endpoints.values())
        else:
            show_type, arg = arg.split(' ', 1)
            for endpoint in self.endpoints.values():
                if show_type == 'state':
                    if arg == 'active' and endpoint.state != 'inactive':
                        endpoints.append(endpoint)
                    elif arg == 'ignored' and endpoint.ignore:
                        endpoints.append(endpoint)
                    elif endpoint.state == arg:
                        endpoints.append(endpoint)
                elif show_type in ['os', 'behavior', 'role']:
                    mac_addresses = endpoint.metadata.get(
                        'mac_addresses', None)
                    endpoint_mac = endpoint.endpoint_data['mac']
                    if endpoint_mac and mac_addresses and endpoint_mac in mac_addresses:
                        timestamps = mac_addresses[endpoint_mac]
                        try:
                            newest = sorted(
                                [timestamp for timestamp in timestamps])[-1]
                            newest = timestamps[newest]
                        except IndexError:
                            newest = None
                        if newest:
                            if 'labels' in newest:
                                if arg.replace('-', ' ') == newest['labels'][0].lower():
                                    endpoints.append(endpoint)
                            if 'behavior' in newest:
                                if arg == newest['behavior'].lower():
                                    endpoints.append(endpoint)

                    # filter by operating system
                    for ip_field in MACHINE_IP_FIELDS:
                        ip_addresses_field = '_'.join((ip_field, 'addresses'))
                        ip_addresses = endpoint.metadata.get(
                            ip_addresses_field, None)
                        machine_ip = endpoint.endpoint_data.get(ip_field, None)
                        if machine_ip and ip_addresses and machine_ip in ip_addresses:
                            metadata = ip_addresses[machine_ip]
                            os = metadata.get('os', None)
                            if os and os.lower() == arg:
                                endpoints.append(endpoint)
        return endpoints

    def check_endpoints(self, messages=None):
        if not self.sdnc:
            return

        retval = {}
        retval['machines'] = None
        retval['resp'] = 'bad'

        current = None
        parsed = None

        try:
            current = self.sdnc.get_endpoints(messages=messages)
            parsed = self.sdnc.format_endpoints(
                current, self.controller['URI'])
            retval['machines'] = parsed
            retval['resp'] = 'ok'
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to {0} because {1}.'.format(
                    self.controller['URI'], e))
            retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.find_new_machines(parsed)

    @staticmethod
    def _diff_machine(machine_a, machine_b):

        def _machine_strlines(machine):
            return str(json.dumps(machine, indent=2)).splitlines()

        machine_a_strlines = _machine_strlines(machine_a)
        machine_b_strlines = _machine_strlines(machine_b)
        return '\n'.join(difflib.unified_diff(
            machine_a_strlines, machine_b_strlines, n=1))

    @staticmethod
    def _parse_machine_ip(machine):
        machine_ip_data = {}
        for ip_field, fields in MACHINE_IP_FIELDS.items():
            try:
                raw_field = machine.get(ip_field, None)
                machine_ip = ipaddress.ip_address(raw_field)
                machine_subnet = ipaddress.ip_network(machine_ip).supernet(
                    new_prefix=MACHINE_IP_PREFIXES[ip_field])
            except ValueError:
                machine_ip = None
                machine_subnet = None
            machine_ip_data[ip_field] = ''
            if machine_ip:
                machine_ip_data.update({
                    ip_field: str(machine_ip),
                    '_'.join((ip_field, 'rdns')): get_rdns_lookup(str(machine_ip)),
                    '_'.join((ip_field, 'subnet')): str(machine_subnet)})
            for field in fields:
                if field not in machine_ip_data:
                    machine_ip_data[field] = NO_DATA
        return machine_ip_data

    @staticmethod
    def merge_machine_ip(old_machine, new_machine):
        for ip_field, fields in MACHINE_IP_FIELDS.items():
            ip = new_machine.get(ip_field, None)
            old_ip = old_machine.get(ip_field, None)
            if not ip and old_ip:
                new_machine[ip_field] = old_ip
                for field in fields:
                    if field in old_machine:
                        new_machine[field] = old_machine[field]

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        change_acls = False

        for machine in machines:
            machine['ether_vendor'] = get_ether_vendor(
                machine['mac'], '/poseidon/poseidon/metadata/nmap-mac-prefixes.txt')
            machine.update(self._parse_machine_ip(machine))
            if 'controller_type' not in machine:
                machine.update({
                    'controller_type': 'none',
                    'controller': ''})
            trunk = False
            for sw in self.trunk_ports:
                if sw == machine['segment'] and self.trunk_ports[sw].split(',')[1] == str(machine['port']) and self.trunk_ports[sw].split(',')[0] == machine['mac']:
                    trunk = True

            h = Endpoint.make_hash(machine, trunk=trunk)
            ep = self.endpoints.get(h, None)
            if ep is None:
                change_acls = True
                m = endpoint_factory(h)
                m.p_prev_states.append((m.state, int(time.time())))
                m.endpoint_data = deepcopy(machine)
                self.endpoints[m.name] = m
                self.logger.info(
                    'Detected new endpoint: {0}:{1}'.format(m.name, machine))
            else:
                self.merge_machine_ip(ep.endpoint_data, machine)

            if ep and ep.endpoint_data != machine and not ep.ignore:
                diff_txt = self._diff_machine(ep.endpoint_data, machine)
                self.logger.info(
                    'Endpoint changed: {0}:{1}'.format(h, diff_txt))
                change_acls = True
                ep.endpoint_data = deepcopy(machine)
                if ep.state == 'inactive' and machine['active'] == 1:
                    if ep.p_next_state in ['known', 'abnormal']:
                        ep.trigger(ep.p_next_state)  # pytype: disable=attribute-error
                    else:
                        ep.unknown()  # pytype: disable=attribute-error
                    ep.p_prev_states.append((ep.state, int(time.time())))
                elif ep.state != 'inactive' and machine['active'] == 0:
                    if ep.state in ['mirroring', 'reinvestigating']:
                        self.unmirror_endpoint(ep)
                        if ep.state == 'mirroring':
                            ep.p_next_state = 'mirror'
                        elif ep.state == 'reinvestigating':
                            ep.p_next_state = 'reinvestigate'
                    if ep.state in ['known', 'abnormal']:
                        ep.p_next_state = ep.state
                    ep.inactive()  # pytype: disable=attribute-error
                    ep.p_prev_states.append((ep.state, int(time.time())))

        if change_acls and self.controller['AUTOMATED_ACLS']:
            status = Actions(None, self.sdnc).update_acls(
                rules_file=self.controller['RULES_FILE'],
                endpoints=self.endpoints.values())
            if isinstance(status, list):
                self.logger.info(
                    'Automated ACLs did the following: {0}'.format(status[1]))
                for item in status[1]:
                    machine = {'mac': item[1],
                               'segment': item[2], 'port': item[3]}
                    h = Endpoint.make_hash(machine)
                    ep = self.endpoints.get(h, None)
                    if ep:
                        ep.acl_data.append(
                            ((item[0], item[4], item[5]), int(time.time())))
        self.store_endpoints()
        self.get_stored_endpoints()

    def store_endpoints(self):
        ''' store current endpoints in Redis. '''
        self.prc.store_endpoints(self.endpoints)


class Monitor:

    def __init__(self, skip_rabbit):
        self.faucet_event = []
        self.m_queue = queue.Queue()
        self.job_queue = queue.Queue()
        self.skip_rabbit = skip_rabbit
        self.logger = logger
        self.rabbit_channel_connection_local = None
        self.rabbit_channel_connection_local_fa = None

        # get config options
        self.controller = Config().get_config()

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
        self.s = SDNConnect(self.controller)

        # schedule periodic scan of endpoints thread
        self.schedule.every(self.controller['scan_frequency']).seconds.do(self.schedule_job_kickurl)

        # schedule periodic reinvestigations thread
        self.schedule.every(self.controller['reinvestigation_frequency']).seconds.do(self.schedule_job_reinvestigation)

        # schedule all threads
        self.schedule_thread = threading.Thread(
            target=partial(
                schedule_thread_worker,
                schedule=self.schedule),
            name='st_worker')

    def job_kickurl(self):
        self.s.check_endpoints(messages=self.faucet_event)
        del self.faucet_event[:]
        try:
            # get current state
            req = requests.get(
                'http://poseidon-api:8000/v1/network_full', timeout=10)
            # send results to prometheus
            hosts = req.json()['dataset']
            self.prom.update_metrics(hosts)
        except requests.exceptions.ConnectionError as e:
            self.logger.debug(
                'Unable to get current state and send it to Prometheus because: {0}'.format(str(e)))
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Unable to get current state and send it to Prometheus because: {0}'.format(str(e)))

    def job_reinvestigation(self):
        ''' put endpoints into the reinvestigation state if possible '''

        def trigger_reinvestigation(candidates):
            # get random order of things that are known
            for _ in range(self.controller['max_concurrent_reinvestigations'] - self.s.investigations):
                if len(candidates) > 0:
                    chosen = candidates.pop()
                    self.logger.info('Starting reinvestigation on: {0} {1}'.format(
                        chosen.name, chosen.state))
                    chosen.reinvestigate()
                    chosen.p_prev_states.append(
                        (chosen.state, int(time.time())))
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

    def format_rabbit_message(self, item):
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
                    self.s.prc.store_p0f_result(my_obj)
                elif tool == 'networkml':
                    self.s.prc.store_tool_result(my_obj, 'networkml')
                    for name, message in data.items():
                        endpoint = self.s.endpoints.get(name, None)
                        if endpoint:
                            endpoint.trigger('unknown')
                            endpoint.p_next_state = None
                            endpoint.p_prev_states.append(
                                (endpoint.state, int(time.time())))
                            if message.get('valid', False):
                                return (data, None)
                            break
            return ({}, None)

        def handler_action_ignore(my_obj):
            for name in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = True
            return ({}, None)

        def handler_action_clear_ignored(my_obj):
            for name in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = False
            return ({}, None)

        def handler_action_change(my_obj):
            for name, state in my_obj:
                endpoint = self.s.endpoints.get(name, None)
                if endpoint:
                    try:
                        if (state != 'mirror' and state != 'reinvestigate' and
                                (endpoint.state == 'mirroring' or endpoint.state == 'reinvestigating')):
                            self.s.unmirror_endpoint(endpoint)
                        endpoint.trigger(state)
                        endpoint.p_next_state = None
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                        if endpoint.state == 'mirroring' or endpoint.state == 'reinvestigating':
                            self.s.mirror_endpoint(endpoint)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to change endpoint {0} because: {1}'.format(endpoint.name, str(e)))
            return ({}, None)

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
            return ({}, None)

        def handler_action_remove(my_obj):
            remove_list = [name for name in my_obj]
            return ({}, remove_list)

        def handler_action_remove_ignored(_my_obj):
            remove_list = [
                endpoint.name for endpoint in self.s.endpoints.values()
                if endpoint.ignore]
            return ({}, remove_list)

        def handler_action_remove_inactives(_my_obj):
            remove_list = [
                endpoint.name for endpoint in self.s.endpoints.values()
                if endpoint.state == 'inactive']
            return ({}, remove_list)

        def handler_faucet_event(my_obj):
            self.logger.debug('FAUCET Event:{0}'.format(my_obj))
            self.faucet_event.append(my_obj)
            return (my_obj, None)

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
        if handler is None:
            self.logger.error(
                'no handler for routing_key {0}'.format(routing_key))
        else:
            ret_val, remove_list = handler(my_obj)
            self.update_routing_key_time(routing_key)
            if remove_list:
                for endpoint_name in remove_list:
                    if endpoint_name in self.s.endpoints:
                        del self.s.endpoints[endpoint_name]
            return (ret_val, True)

        return ({}, False)

    def schedule_mirroring(self):
        queued_endpoints = [
            endpoint for endpoint in self.s.endpoints.values()
            if not endpoint.ignore and endpoint.state == 'queued' and endpoint.p_next_state != 'inactive']
        self.s.investigations = len([
            endpoint for endpoint in self.s.endpoints.values()
            if endpoint.state in ['mirroring', 'reinvestigating']])
        # mirror things in the order they got added to the queue
        queued_endpoints = sorted(
            queued_endpoints, key=lambda x: x.p_prev_states[-1][1])

        investigation_budget = max(
            self.controller['max_concurrent_reinvestigations'] -
            self.s.investigations,
            0)
        self.logger.debug('investigations {0}, budget {1}, queued {2}'.format(
            str(self.s.investigations), str(investigation_budget), str(len(queued_endpoints))))

        for endpoint in queued_endpoints[:investigation_budget]:
            endpoint.trigger(endpoint.p_next_state)
            endpoint.p_next_state = None
            endpoint.p_prev_states.append(
                (endpoint.state, int(time.time())))
            self.s.mirror_endpoint(endpoint)

        for endpoint in self.s.endpoints.values():
            if not endpoint.ignore:
                if self.s.sdnc:
                    if endpoint.state == 'unknown':
                        endpoint.p_next_state = 'mirror'
                        endpoint.queue()
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                    elif endpoint.state in ['mirroring', 'reinvestigating']:
                        cur_time = int(time.time())
                        # timeout after 2 times the reinvestigation frequency
                        # in case something didn't report back, put back in an
                        # unknown state
                        if cur_time - endpoint.p_prev_states[-1][1] > 2*self.controller['reinvestigation_frequency']:
                            self.logger.debug(
                                'timing out: {0} and setting to unknown'.format(endpoint.name))
                            self.s.unmirror_endpoint(endpoint)
                            endpoint.unknown()
                            endpoint.p_prev_states.append(
                                (endpoint.state, int(time.time())))
                else:
                    if endpoint.state != 'known':
                        endpoint.known()

    def schedule_coprocessing(self):
        queued_endpoints = [
            endpoint for endpoint in self.s.endpoints.values()
            if not endpoint.copro_ignore and endpoint.copro_state == 'copro_queued']
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
            endpoint.trigger(endpoint.p_next_copro_state)
            endpoint.p_next_copro_state = None
            endpoint.p_prev_copro_states.append(
                (endpoint.copro_state, int(time.time())))
            self.s.coprocess_endpoint(endpoint)

        for endpoint in self.s.endpoints.values():
            if not endpoint.copro_ignore:
                if self.s.sdnc:
                    if endpoint.copro_state == 'copro_unknown':
                        endpoint.p_next_copro_state = 'copro_coprocessing'
                        endpoint.copro_queue()
                        endpoint.p_prev_copro_states.append(
                            (endpoint.copro_state, int(time.time())))
                    elif endpoint.copro_state in ['copro_coprocessing']:
                        cur_time = int(time.time())
                        # timeout after 2 times the reinvestigation frequency
                        # in case something didn't report back, put back in an
                        # unknown state
                        if cur_time - endpoint.p_prev_copro_states[-1][1] > 2*self.controller['coprocessing_frequency']:
                            self.logger.debug(
                                'timing out: {0} and setting to unknown'.format(endpoint.name))
                            self.s.uncoprocess_endpoint(endpoint)
                            endpoint.copro_unknown()
                            endpoint.p_prev_copro_states.append(
                                (endpoint.copro_state, int(time.time())))
                else:
                    if endpoint.state != 'copro_nominal':
                        endpoint.copro_nominal()

    def process(self):
        global CTRL_C
        signal.signal(signal.SIGINT, partial(self.signal_handler))
        while not CTRL_C['STOP']:
            time.sleep(1)
            found_work, item = self.get_q_item()
            if found_work:
                self.format_rabbit_message(item)
            else:
                if not self.job_queue.empty():
                    schedule_func = self.job_queue.get()
                    self.logger.info('calling %s' % schedule_func)
                    schedule_func()

            self.schedule_mirroring()

        self.s.store_endpoints()

    def get_q_item(self):
        '''
        attempt to get a work item from the queue
        m_queue -> (routing_key, body)
        a read from get_q_item should be of the form
        (boolean,(routing_key, body))
        '''
        found_work = False
        item = None
        global CTRL_C

        if not CTRL_C['STOP']:
            try:
                item = self.m_queue.get(False)
                found_work = True
                self.m_queue.task_done()
            except queue.Empty:  # pragma: no cover
                pass

        return (found_work, item)

    def shutdown(self):
        ''' gracefully shut down. '''
        self.s.clear_filters()
        for job in self.schedule.jobs:
            self.logger.debug('shutdown :{0}'.format(job))
            self.schedule.cancel_job(job)
        if self.rabbit_channel_connection_local:
            self.rabbit_channel_connection_local.close()
        if self.rabbit_channel_connection_local_fa:
            self.rabbit_channel_connection_local_fa.close()
        self.logger.debug('SHUTTING DOWN')
        self.logger.debug('EXITING')
        sys.exit()

    def signal_handler(self, _signal, _frame):
        ''' hopefully eat a CTRL_C and signal system shutdown '''
        global CTRL_C
        CTRL_C['STOP'] = True
        self.logger.debug('CTRL-C: {0}'.format(CTRL_C))
        try:
            self.shutdown()
        except Exception as e:  # pragma: no cover
            self.logger.debug(
                'Failed to handle signal properly because: {0}'.format(str(e)))


def main(skip_rabbit=False):  # pragma: no cover
    # setup rabbit and monitoring of the network
    pmain = Monitor(skip_rabbit=skip_rabbit)
    if not skip_rabbit:
        rabbit = Rabbit()
        host = pmain.controller['rabbit_server']
        port = int(pmain.controller['rabbit_port'])
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_main'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    if pmain.controller['FA_RABBIT_ENABLED']:
        rabbit = Rabbit()
        host = pmain.controller['FA_RABBIT_HOST']
        port = pmain.controller['FA_RABBIT_PORT']
        exchange = pmain.controller['FA_RABBIT_EXCHANGE']
        queue_name = 'poseidon_main'
        binding_key = [pmain.controller['FA_RABBIT_ROUTING_KEY']+'.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local_fa = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    pmain.schedule_thread.start()

    # loop here until told not to
    try:
        pmain.process()
    except Exception as e:
        logger.error('process() exception: {0}'.format(str(e)))

    pmain.shutdown()


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
