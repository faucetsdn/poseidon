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


class Endpoint:

    states = ['known', 'unknown', 'mirroring', 'inactive', 'abnormal',
              'shutdown', 'reinvestigating', 'queued']

    transitions = [
        {'trigger': 'mirror', 'source': 'unknown',
            'dest': 'mirroring', 'before': 'update_state_history'},
        {'trigger': 'queue', 'source': 'unknown',
            'dest': 'queued', 'before': 'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'known',
            'dest': 'reinvestigating', 'before': 'update_state_history'},
        {'trigger': 'queue', 'source': 'known',
            'dest': 'queued', 'before': 'update_state_history'},
        {'trigger': 'shutdown', 'source': 'abnormal',
            'dest': 'shutdown', 'before': 'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'abnormal',
            'dest': 'reinvestigating', 'before': 'update_state_history'},
        {'trigger': 'queue', 'source': 'abnormal',
            'dest': 'queued', 'before': 'update_state_history'},
        {'trigger': 'mirror', 'source': 'queued',
            'dest': 'mirroring', 'before': 'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'queued',
            'dest': 'reinvestigating', 'before': 'update_state_history'},
        # check all states and put into known/unknown/abnormal/inactive to account for external updates
        {'trigger': 'known', 'source': 'known',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'known',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'known',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'known',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'unknown',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'unknown',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'unknown',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'unknown',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'mirroring',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'mirroring',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'mirroring',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'mirroring',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'inactive',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'inactive',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'inactive',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'inactive',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'abnormal',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'abnormal',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'abnormal',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'abnormal',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'shutdown',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'shutdown',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'shutdown',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'shutdown',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'reinvestigating',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'reinvestigating',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'reinvestigating',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'reinvestigating',
            'dest': 'inactive', 'before': 'update_state_history'},
        {'trigger': 'known', 'source': 'queued',
            'dest': 'known', 'before': 'update_state_history'},
        {'trigger': 'unknown', 'source': 'queued',
            'dest': 'unknown', 'before': 'update_state_history'},
        {'trigger': 'abnormal', 'source': 'queued',
            'dest': 'abnormal', 'before': 'update_state_history'},
        {'trigger': 'inactive', 'source': 'queued',
            'dest': 'inactive', 'before': 'update_state_history'}
    ]

    copro_states = ['unknown', 'coprocessing', 'nominal', 'suspicious', 'queued']

    copro_transitions = [
        {'trigger': 'coprocess', 'source': 'unknown',
            'dest': 'coprocessing', 'before': 'update_copro_history'},
        {'trigger': 'queue', 'source': 'unknown',
            'dest': 'queued', 'before': 'update_copro_history'},  
        {'trigger': 'coprocess', 'source': 'queued',
            'dest': 'coprocessing', 'before': 'update_copro_history'},
        {'trigger': 'nominal', 'source': 'coprocessing',
            'dest': 'nominal', 'before': 'update_copro_history'},
        {'trigger': 'suspicious', 'source': 'coprocessing',
            'dest': 'suspicious', 'before': 'update_copro_history'},
        {'trigger': 'queue', 'source': 'nominal',
            'dest': 'queued', 'before': 'update_copro_history'},  
        {'trigger': 'coprocess', 'source': 'nominal',
            'dest': 'coprocessing', 'before': 'update_copro_history'},
        {'trigger': 'queue', 'source': 'suspicious',
            'dest': 'queued', 'before': 'update_copro_history'},  
        {'trigger': 'coprocess', 'source': 'suspicious',
            'dest': 'coprocessing', 'before': 'update_copro_history'},

    ]

    def __init__(self, hashed_val):
        self.name = hashed_val.strip()
        self.ignore = False
        self.copro_ignores = False
        self.endpoint_data = None
        self.p_next_state = None
        self.p_prev_states = []
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
            'p_prev_states': self.p_prev_states,
            'acl_data': self.acl_data,
            'metadata': self.metadata,
            'history': self.history,
        }
        return str(json.dumps(endpoint_d))

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
        self._add_history_entry(
            HistoryTypes.STATE_CHANGE, time.time(),
            'State changed from {0} to {1}'.format(event_data.transition.source, event_data.transition.dest))

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
    copro_machine = Machine(
        model=endpoint,
        states=Endpoint.copro_states,
        transitions=Endpoint.copro_transitions,
        initial='unknown',
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
        self.endpoint.p_prev_states = e['p_prev_states']

    def get_endpoint(self):
        return self.endpoint
