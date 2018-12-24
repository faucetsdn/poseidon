# -*- coding: utf-8 -*-
"""
Created on 3 December 2018
@author: Charlie Lewis
"""
import hashlib
import json

from transitions import Machine


class EndpointDecoder(object):

    def __init__(self, endpoint):
        e = json.loads(endpoint)
        self.endpoint = Endpoint(e['name'])
        self.endpoint.state = e['state']
        self.endpoint.endpoint_data = e['endpoint_data']
        self.endpoint.p_next_state = e['p_next_state']
        self.endpoint.p_prev_states = e['p_prev_states']

    def get_endpoint(self):
        return self.endpoint


class Endpoint(object):

    states = ['known', 'unknown', 'mirroring', 'inactive', 'abnormal',
              'shutdown', 'reinvestigating', 'queued']

    transitions = [
        {'trigger': 'mirror', 'source': 'unknown', 'dest': 'mirroring'},
        {'trigger': 'queue', 'source': 'unknown', 'dest': 'queued'},
        {'trigger': 'reinvestigate', 'source': 'known', 'dest': 'reinvestigating'},
        {'trigger': 'queue', 'source': 'known', 'dest': 'queued'},
        {'trigger': 'shutdown', 'source': 'abnormal', 'dest': 'shutdown'},
        {'trigger': 'reinvestigate', 'source': 'abnormal', 'dest': 'reinvestigating'},
        {'trigger': 'queue', 'source': 'abnormal', 'dest': 'queued'},
        {'trigger': 'mirror', 'source': 'queued', 'dest': 'mirroring'},
        {'trigger': 'reinvestigate', 'source': 'queued', 'dest': 'reinvestigating'},
        # check all states and put into known/unknown/abnormal/inactive to account for external updates
        {'trigger': 'known', 'source': 'known', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'known', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'known', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'known', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'unknown', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'unknown', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'unknown', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'unknown', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'mirroring', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'mirroring', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'mirroring', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'mirroring', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'inactive', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'inactive', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'inactive', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'inactive', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'abnormal', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'abnormal', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'abnormal', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'abnormal', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'shutdown', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'shutdown', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'shutdown', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'shutdown', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'reinvestigating', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'reinvestigating', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'reinvestigating', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'reinvestigating', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'queued', 'dest': 'known'},
        {'trigger': 'unknown', 'source': 'queued', 'dest': 'unknown'},
        {'trigger': 'abnormal', 'source': 'queued', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'queued', 'dest': 'inactive'}
    ]

    def __init__(self, hashed_val):
        # Initialize the state machine
        self.machine = Machine(model=self, states=Endpoint.states,
                               transitions=Endpoint.transitions, initial='unknown')
        self.machine.name = hashed_val[:8]+' '
        self.name = hashed_val
        self.endpoint_data = None
        self.p_next_state = None
        self.p_prev_states = []

    def encode(self):
        endpoint_d = {}
        endpoint_d['name'] = self.name
        endpoint_d['state'] = self.state
        endpoint_d['endpoint_data'] = self.endpoint_data
        endpoint_d['p_next_state'] = self.p_next_state
        endpoint_d['p_prev_states'] = self.p_prev_states
        return str(json.dumps(endpoint_d))

    @staticmethod
    def make_hash(machine):
        ''' hash the unique metadata parts of an endpoint '''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        for word in ['tenant', 'mac', 'segment']:
            pre_h = pre_h + str(machine.get(word, 'missing'))
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h
