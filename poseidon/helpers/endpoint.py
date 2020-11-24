# -*- coding: utf-8 -*-
"""
Created on 3 December 2018
@author: Charlie Lewis
"""
import hashlib
import json
import time

from transitions import Machine

MACHINE_IP_FIELDS = {
    'ipv4': ('ipv4_rdns', 'ipv4_subnet'),
    'ipv6': ('ipv6_rdns', 'ipv6_subnet')}
MACHINE_IP_PREFIXES = {
    'ipv4': 24, 'ipv6': 64}


class HistoryTypes():
    STATE_CHANGE = 'State Change'
    ACL_CHANGE = 'ACL Change'
    PROPERTY_CHANGE = 'Property Change'
    COPRO_CHANGE = 'Coprocessor Change'


def transit_wrap(trigger, source, dest, before=None, after=None):
    transit_dict = {'trigger': trigger, 'source': source, 'dest': dest}
    if before is not None:
        transit_dict['before'] = before
    if after is not None:
        transit_dict['after'] = after
    return transit_dict


def endpoint_transit_wrap(trigger, source, dest):
    return transit_wrap(trigger, source, dest, before='update_state_history')


def endpoint_copro_transit_wrap(trigger, source, dest):
    return transit_wrap(trigger, source, dest, before='update_copro_history')


class Endpoint:

    states = ['known', 'unknown', 'mirroring', 'inactive', 'abnormal',
              'shutdown', 'reinvestigating', 'queued']

    transitions = [
        endpoint_transit_wrap('mirror', 'unknown', 'mirroring'),
        endpoint_transit_wrap('queue', 'unknown', 'queued'),
        endpoint_transit_wrap('reinvestigate', 'known', 'reinvestigating'),
        endpoint_transit_wrap('queue', 'known', 'queued'),
        endpoint_transit_wrap('shutdown', 'abnormal', 'shutdown'),
        endpoint_transit_wrap('reinvestigate', 'abnormal', 'reinvestigating'),
        endpoint_transit_wrap('queue', 'abnormal', 'queued'),
        endpoint_transit_wrap('mirror', 'queued', 'mirroring'),
        endpoint_transit_wrap('reinvestigate', 'queued', 'reinvestigating'),
        endpoint_transit_wrap('known', 'known', 'known'),
        endpoint_transit_wrap('unknown', 'known', 'unknown'),
        endpoint_transit_wrap('abnormal', 'known', 'abnormal'),
        endpoint_transit_wrap('inactive', 'known', 'inactive'),
        endpoint_transit_wrap('known', 'unknown', 'known'),
        endpoint_transit_wrap('unknown', 'unknown', 'unknown'),
        endpoint_transit_wrap('abnormal', 'unknown', 'abnormal'),
        endpoint_transit_wrap('inactive', 'unknown', 'inactive'),
        endpoint_transit_wrap('known', 'mirroring', 'known'),
        endpoint_transit_wrap('unknown', 'mirroring', 'unknown'),
        endpoint_transit_wrap('abnormal', 'mirroring', 'abnormal'),
        endpoint_transit_wrap('inactive', 'mirroring', 'inactive'),
        endpoint_transit_wrap('known', 'inactive', 'known'),
        endpoint_transit_wrap('unknown', 'inactive', 'unknown'),
        endpoint_transit_wrap('abnormal', 'inactive', 'abnormal'),
        endpoint_transit_wrap('inactive', 'inactive', 'inactive'),
        endpoint_transit_wrap('known', 'abnormal', 'known'),
        endpoint_transit_wrap('unknown', 'abnormal', 'unknown'),
        endpoint_transit_wrap('abnormal', 'abnormal', 'abnormal'),
        endpoint_transit_wrap('inactive', 'abnormal', 'inactive'),
        endpoint_transit_wrap('known', 'shutdown', 'known'),
        endpoint_transit_wrap('unknown', 'shutdown', 'unknown'),
        endpoint_transit_wrap('abnormal', 'shutdown', 'abnormal'),
        endpoint_transit_wrap('inactive', 'shutdown', 'inactive'),
        endpoint_transit_wrap('known', 'reinvestigating', 'known'),
        endpoint_transit_wrap('unknown', 'reinvestigating', 'unknown'),
        endpoint_transit_wrap('abnormal', 'reinvestigating', 'abnormal'),
        endpoint_transit_wrap('inactive', 'reinvestigating', 'inactive'),
        endpoint_transit_wrap('known', 'queued', 'known'),
        endpoint_transit_wrap('unknown', 'queued', 'unknown'),
        endpoint_transit_wrap('abnormal', 'queued', 'abnormal'),
        endpoint_transit_wrap('inactive', 'queued', 'inactive'),
    ]

    copro_states = ['copro_unknown', 'copro_coprocessing',
                    'copro_nominal', 'copro_suspicious', 'copro_queued']

    copro_transitions = [
        endpoint_copro_transit_wrap('copro_coprocess', 'copro_unknown', 'copro_coprocessing'),
        endpoint_copro_transit_wrap('copro_queue', 'copro_unknown', 'copro_queued'),
        endpoint_copro_transit_wrap('copro_coprocess', 'copro_queued', 'copro_coprocessing'),
        endpoint_copro_transit_wrap('copro_nominal', 'copro_coprocessing', 'copro_nominal'),
        endpoint_copro_transit_wrap('copro_suspicious', 'copro_coprocessing', 'copro_suspicious'),
        endpoint_copro_transit_wrap('copro_queue', 'copro_nominal', 'copro_queued'),
        endpoint_copro_transit_wrap('copro_coprocess', 'copro_nominal', 'copro_coprocessing'),
        endpoint_copro_transit_wrap('copro_queue', 'copro_suspicious', 'copro_queued'),
        endpoint_copro_transit_wrap('copro_coprocess', 'copro_suspicious', 'copro_coprocessing'),
    ]

    def __init__(self, hashed_val):
        self.name = hashed_val.strip()
        self.ignore = False
        self.copro_ignores = False
        self.endpoint_data = None
        self.p_next_state = None
        self.p_prev_state = None
        self.p_next_copro_state = None
        self.p_prev_copross_states = []
        self.acl_data = []
        self.metadata = {}
        self.history = []
        self.state = None
        self.copro_state = None

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
            'history': self.history,
        }
        return str(json.dumps(endpoint_d))

    def state_time(self):
        return self.p_prev_state[1]

    def default(self):
        if not self.ignore:
            if self.state != 'inactive':
                if self.state == 'mirroring':
                    self.p_next_state = 'mirror'
                elif self.state == 'reinvestigating':
                    self.p_next_state = 'reinvestigate'
                elif self.state == 'queued':
                    self.p_next_state = 'queue'
                elif self.state in ['known', 'abnormal']:
                    self.p_next_state = self.state
                self.endpoint_data['active'] = 0
                self.inactive()  # pytype: disable=attribute-error

    def _add_history_entry(self, entry_type, timestamp, message):
        self.history.append(
            {'type': entry_type, 'timestamp': timestamp, 'message': message})

    def update_copro_history(self, event_data):
        self._add_history_entry(
            HistoryTypes.COPRO_CHANGE, time.time(),
            'Coprocessing state changed from {0} to {1}'.format(event_data.transition.source, event_data.transition.dest))

    def update_acl_history(self, event_data, added_acls, removed_acls):
        message = ''
        if added_acls and len(added_acls) > 0:
            message += 'Added the following ACLs: ' + \
                ', '.join(added_acls) + '\r\n'
        if len(message) > 0:
            message += 'and r'
        if removed_acls and len(removed_acls) > 0:
            message += 'R' if len(message) == 0 else ''
            message += 'emoved the following ACLs:' + ', '.join(removed_acls)

        self._add_history_entry(HistoryTypes.ACL_CHANGE, time.time(),
                                'State changed from {0} to {1}'.format(event_data.transition.source, event_data.transition.dest))

    def update_property_history(self, entry_type, timestamp, field_name, old_value, new_value):
        self._add_history_entry(entry_type, timestamp,
                                'Property {0} changed from {1} to {2}'.format(field_name, old_value, new_value))

    def update_state_history(self, event_data):
        self.p_prev_state = (event_data.transition.dest, int(time.time()))
        self._add_history_entry(
            HistoryTypes.STATE_CHANGE, time.time(),
            'State changed from {0} to {1}'.format(
                event_data.transition.source, event_data.transition.dest))

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
        states=Endpoint.states,
        transitions=Endpoint.transitions,
        initial='unknown',
        send_event=True)
    machine.name = endpoint.name[:8]+' '
    endpoint.machine = machine
    copro_endpoint = Endpoint(hashed_val)
    copro_machine = Machine(
        model=copro_endpoint,
        states=Endpoint.copro_states,
        transitions=Endpoint.copro_transitions,
        initial='copro_unknown',
        send_event=True)
    copro_machine.name = endpoint.name[:8]+'_copro'
    endpoint.copro_machine = copro_machine
    return endpoint


class EndpointDecoder:

    def __init__(self, endpoint):
        e = json.loads(endpoint)
        self.endpoint = endpoint_factory(e['name'])
        self.endpoint.state = e['state']
        self.endpoint.copro_state = e['copro_state']
        if 'ignore' in e:
            if e['ignore']:
                self.endpoint.ignore = True
            else:
                self.endpoint.ignore = False
        else:
            self.endpoint.ignore = False
        if 'metadata' in e:
            self.endpoint.metadata = e['metadata']
        else:
            self.endpoint.metadata = {}
        if 'history' in e:
            self.endpoint.history = e['history']
        else:
            self.endpoint.history = []
        if 'acl_data' in e:
            self.endpoint.acl_data = e['acl_data']
        else:
            self.endpoint.acl_data = []
        self.endpoint.endpoint_data = e['endpoint_data']
        self.endpoint.p_next_state = e['p_next_state']
        self.endpoint.p_prev_state = e['p_prev_state']

    def get_endpoint(self):
        return self.endpoint
