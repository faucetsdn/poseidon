# -*- coding: utf-8 -*-
"""
Created on 3 December 2018
@author: Charlie Lewis
"""
import hashlib
import json
import time

from poseidon_core.constants import NO_DATA
from transitions import Machine

MACHINE_IP_FIELDS = {
    'ipv4': ('ipv4_rdns', 'ipv4_subnet'),
    'ipv6': ('ipv6_rdns', 'ipv6_subnet')}
MACHINE_IP_PREFIXES = {
    'ipv4': 24, 'ipv6': 64}


def transit_wrap(trigger, source, dest, before=None, after=None):
    transit_dict = {'trigger': trigger, 'source': source, 'dest': dest}
    if before is not None:
        transit_dict['before'] = before
    if after is not None:
        transit_dict['after'] = after
    return transit_dict


def endpoint_transit_wrap(trigger, source, dest):
    return transit_wrap(trigger, source, dest, after='_update_state_time')


def endpoint_copro_transit_wrap(trigger, source, dest):
    return transit_wrap(trigger, source, dest, after='_update_copro_state_time')


class Endpoint:

    states = ['known', 'unknown', 'operating', 'queued']

    transitions = [
        endpoint_transit_wrap('operate', 'unknown', 'operating'),
        endpoint_transit_wrap('queue', 'unknown', 'queued'),
        endpoint_transit_wrap('operate', 'known', 'operating'),
        endpoint_transit_wrap('queue', 'known', 'queued'),
        endpoint_transit_wrap('operate', 'queued', 'operating'),
        endpoint_transit_wrap('known', 'known', 'known'),
        endpoint_transit_wrap('unknown', 'known', 'unknown'),
        endpoint_transit_wrap('known', 'unknown', 'known'),
        endpoint_transit_wrap('unknown', 'unknown', 'unknown'),
        endpoint_transit_wrap('known', 'operating', 'known'),
        endpoint_transit_wrap('unknown', 'operating', 'unknown'),
        endpoint_transit_wrap('known', 'queued', 'known'),
        endpoint_transit_wrap('unknown', 'queued', 'unknown'),
    ]

    copro_states = ['copro_unknown', 'copro_coprocessing',
                    'copro_nominal', 'copro_suspicious', 'copro_queued']

    copro_transitions = [
        endpoint_copro_transit_wrap(
            'copro_coprocess', 'copro_unknown', 'copro_coprocessing'),
        endpoint_copro_transit_wrap(
            'copro_queue', 'copro_unknown', 'copro_queued'),
        endpoint_copro_transit_wrap(
            'copro_coprocess', 'copro_queued', 'copro_coprocessing'),
        endpoint_copro_transit_wrap(
            'copro_nominal', 'copro_coprocessing', 'copro_nominal'),
        endpoint_copro_transit_wrap(
            'copro_nominal', 'copro_queued', 'copro_nominal'),
        endpoint_copro_transit_wrap(
            'copro_suspicious', 'copro_coprocessing', 'copro_suspicious'),
        endpoint_copro_transit_wrap(
            'copro_queue', 'copro_nominal', 'copro_queued'),
        endpoint_copro_transit_wrap(
            'copro_coprocess', 'copro_nominal', 'copro_coprocessing'),
        endpoint_copro_transit_wrap(
            'copro_queue', 'copro_suspicious', 'copro_queued'),
        endpoint_copro_transit_wrap(
            'copro_coprocess', 'copro_suspicious', 'copro_coprocessing'),
    ]

    def __init__(self, hashed_val):
        self.name = hashed_val.strip()
        self.ignore = False
        self.copro_ignore = False
        self.endpoint_data = None
        self.p_next_state = None
        self.p_prev_state = None
        self.p_next_copro_state = None
        self.p_prev_copro_state = None
        self.acl_data = []
        self.metadata = {}
        self.state = None
        self.copro_state = None
        self.state_time = 0
        self.copro_state_time = 0
        self.observed_time = 0

    def _update_state_time(self, *args, **kwargs):
        self.state_time = time.time()

    def _update_copro_state_time(self, *args, **kwargs):
        self.copro_state_time = time.time()

    def encode(self):
        endpoint_d = {
            'name': self.name,
            'state': self.state,
            'copro_state': self.copro_state,
            'ignore': self.ignore,
            'endpoint_data': self.endpoint_data,
            'p_next_state': self.p_next_state,
            'p_prev_state': self.p_prev_state,
            'acl_data': self.acl_data,
            'metadata': self.metadata,
            'observed_time': self.observed_time,
        }
        return str(json.dumps(endpoint_d))

    def mac_addresses(self):
        return self.metadata.get('mac_addresses', {})

    def get_roles_confidences_pcap_labels(self):
        top_role = NO_DATA
        second_role = NO_DATA
        third_role = NO_DATA
        top_conf = '0'
        second_conf = '0'
        third_conf = '0'
        pcap_labels = NO_DATA
        for metadata in self.mac_addresses().values():
            classification = metadata.get('classification', {})
            if 'labels' in classification:
                top_role, second_role, third_role = classification['labels'][:3]
            if 'confidences' in classification:
                top_conf, second_conf, third_conf = classification['confidences'][:3]
            metadata_pcap_labels = metadata.get('pcap_labels', None)
            if metadata_pcap_labels:
                pcap_labels = metadata_pcap_labels
        return (top_role, second_role, third_role), (top_conf, second_conf, third_conf), pcap_labels

    def get_ipv4_os(self):
        if 'ipv4_addresses' in self.metadata:
            ipv4 = self.endpoint_data['ipv4']
            for ip, ip_metadata in self.metadata['ipv4_addresses'].items():
                if ip == ipv4:
                    if 'short_os' in ip_metadata:
                        return ip_metadata['short_os']
        return NO_DATA

    def touch(self):
        self.observed_time = time.time()

    def observed_timeout(self, timeout):
        return time.time() - self.observed_time > timeout

    def state_age(self):
        return int(time.time()) - self.state_time

    def state_timeout(self, timeout):
        return self.state_age() > timeout

    def copro_state_age(self):
        return int(time.time()) - self.copro_state_time

    def copro_state_timeout(self, timeout):
        return self.copro_state_age() > timeout

    def queue_next(self, next_state):
        self.p_next_state = next_state
        self.queue()  # pytype: disable=attribute-error

    def machine_trigger(self, state):
        # pytype: disable=attribute-error
        self.machine.events[state].trigger(self)

    def trigger_next(self):
        self.p_prev_state = self.state
        if self.p_next_state:
            self.machine_trigger(self.p_next_state)
            self.p_next_state = None

    def copro_queue_next(self, next_state):
        self.p_next_copro_state = next_state
        self.copro_queue()  # pytype: disable=attribute-error

    def copro_machine_trigger(self, state):
        self.copro_machine.events[state].trigger(
            self)  # pytype: disable=attribute-error

    def copro_trigger_next(self):
        if self.p_next_copro_state:
            self.copro_machine_trigger(self.p_next_copro_state)
            self.p_next_copro_state = None

    def operation_active(self):
        return self.state == 'operating'

    def operation_requested(self, next_state=None):
        if next_state is None:
            next_state = self.p_next_state
        return next_state == 'operate'

    def force_unknown(self):
        self.unknown()  # pytype: disable=attribute-error
        self.p_next_state = None

    def default(self):
        if not self.ignore:
            if self.state != 'unknown':
                if self.state == 'operating':
                    self.p_next_state = 'operate'
                elif self.state == 'queued':
                    self.p_next_state = 'queue'
                elif self.state == 'known':
                    self.p_next_state = self.state
                self.unknown()  # pytype: disable=attribute-error

    @staticmethod
    def make_hash(machine, trunk=False):
        ''' hash the unique metadata parts of an endpoint '''
        h = hashlib.new('ripemd160')
        words = ['tenant', 'mac', 'segment']
        if trunk:
            words.append('ipv4')
            words.append('ipv6')
        pre_h = ''.join([str(machine.get(word, 'missing')) for word in words])
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h


def endpoint_factory(hashed_val):
    endpoint = Endpoint(hashed_val)
    machine = Machine(
        model=endpoint,
        model_attribute='state',
        states=Endpoint.states,
        transitions=Endpoint.transitions,
        initial='unknown',
        send_event=True)
    machine.name = endpoint.name[:8]+' '
    endpoint.machine = machine
    copro_machine = Machine(
        model=endpoint,
        model_attribute='copro_state',
        states=Endpoint.copro_states,
        transitions=Endpoint.copro_transitions,
        initial='copro_unknown',
        send_event=True)
    copro_machine.name = endpoint.name[:8]+'_copro'
    endpoint.copro_machine = copro_machine
    return endpoint


class EndpointDecoder:

    def __init__(self, endpoint):
        if isinstance(endpoint, dict):
            e = endpoint
        else:
            e = json.loads(endpoint)
        self.endpoint = endpoint_factory(e['name'])
        self.endpoint.state = e['state']
        self.endpoint.copro_state = e.get('copro_state', None)
        self.endpoint.ignore = bool(e.get('ignore', False))
        self.endpoint.metadata = e.get('metadata', {})
        self.endpoint.acl_data = e.get('acl_data', [])
        self.endpoint.endpoint_data = e['endpoint_data']
        self.endpoint.p_next_state = e['p_next_state']
        self.endpoint.p_prev_state = e.get('p_prev_state', None)
        self.endpoint.observed_time = e.get('observed_time', 0)

    def get_endpoint(self):
        return self.endpoint
