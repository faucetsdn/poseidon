# -*- coding: utf-8 -*-
"""
Created on 3 December 2018
@author: Charlie Lewis
"""
import hashlib
import json
import time

from enum import Enum, auto
from transitions import Machine

class HistoryTypes():
    STATE_CHANGE = 'State Change'
    ACL_CHANGE = 'ACL Change'

class EndpointDecoder(object):

    def __init__(self, endpoint):
        e = json.loads(endpoint)
        self.endpoint = Endpoint(e['name'])
        self.endpoint.state = e['state']
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
        self.endpoint.endpoint_data = e['endpoint_data']
        self.endpoint.p_next_state = e['p_next_state']
        self.endpoint.p_prev_states = e['p_prev_states']

    def get_endpoint(self):
        return self.endpoint


class Endpoint(object):

    states = ['known', 'unknown', 'mirroring', 'inactive', 'abnormal',
              'shutdown', 'reinvestigating', 'queued']

    transitions = [
        {'trigger': 'mirror', 'source': 'unknown', 'dest': 'mirroring', 'before':'update_state_history'},
        {'trigger': 'queue', 'source': 'unknown', 'dest': 'queued', 'before':'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'known', 'dest': 'reinvestigating', 'before':'update_state_history'},
        {'trigger': 'queue', 'source': 'known', 'dest': 'queued', 'before':'update_state_history'},
        {'trigger': 'shutdown', 'source': 'abnormal', 'dest': 'shutdown', 'before':'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'abnormal', 'dest': 'reinvestigating', 'before':'update_state_history'},
        {'trigger': 'queue', 'source': 'abnormal', 'dest': 'queued', 'before':'update_state_history'},
        {'trigger': 'mirror', 'source': 'queued', 'dest': 'mirroring', 'before':'update_state_history'},
        {'trigger': 'reinvestigate', 'source': 'queued', 'dest': 'reinvestigating', 'before':'update_state_history'},
        # check all states and put into known/unknown/abnormal/inactive to account for external updates
        {'trigger': 'known', 'source': 'known', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'known', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'known', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'known', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'unknown', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'unknown', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'unknown', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'unknown', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'mirroring', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'mirroring', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'mirroring', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'mirroring', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'inactive', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'inactive', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'inactive', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'inactive', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'abnormal', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'abnormal', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'abnormal', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'abnormal', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'shutdown', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'shutdown', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'shutdown', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'shutdown', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'reinvestigating', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'reinvestigating', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'reinvestigating', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'reinvestigating', 'dest': 'inactive', 'before':'update_state_history'},
        {'trigger': 'known', 'source': 'queued', 'dest': 'known', 'before':'update_state_history'},
        {'trigger': 'unknown', 'source': 'queued', 'dest': 'unknown', 'before':'update_state_history'},
        {'trigger': 'abnormal', 'source': 'queued', 'dest': 'abnormal', 'before':'update_state_history'},
        {'trigger': 'inactive', 'source': 'queued', 'dest': 'inactive', 'before':'update_state_history'}
    ]

    def __init__(self, hashed_val):
        # Initialize the state machine
        self.machine = Machine(model=self, states=Endpoint.states,
                               transitions=Endpoint.transitions, initial='unknown', send_event=True)
        self.machine.name = hashed_val[:8]+' '
        self.name = hashed_val
        self.ignore = False
        self.endpoint_data = None
        self.p_next_state = None
        self.p_prev_states = []
        self.metadata = {}
        self.history = []

    def encode(self):
        endpoint_d = {}
        endpoint_d['name'] = self.name
        endpoint_d['state'] = self.state
        endpoint_d['ignore'] = self.ignore
        endpoint_d['endpoint_data'] = self.endpoint_data
        endpoint_d['p_next_state'] = self.p_next_state
        endpoint_d['p_prev_states'] = self.p_prev_states
        endpoint_d['metadata'] = self.metadata
        endpoint_d['history'] = self.history
        return str(json.dumps(endpoint_d))

    def _add_history_entry(self, entry_type, timestamp, message):
        self.history.append({'type':entry_type, 'timestamp': timestamp, 'message': message})

    def update_state_history(self, event_data):
        self._add_history_entry(HistoryTypes.STATE_CHANGE, time.time(), 
            "State changed from {0} to {1}".format(event_data.transition.source, event_data.transition.dest))

    @staticmethod
    def make_hash(machine, trunk=False):
        ''' hash the unique metadata parts of an endpoint '''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        words = ['tenant', 'mac', 'segment']
        if trunk:
            words.append('ipv4')
            words.append('ipv6')
        for word in words:
            pre_h = pre_h + str(machine.get(word, 'missing'))
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h
