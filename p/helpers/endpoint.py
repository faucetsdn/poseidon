# -*- coding: utf-8 -*-
"""
Created on 3 December 2018
@author: Charlie Lewis
"""
from transitions import Machine


class Endpoint(object):

    states = ['known', 'unknown', 'mirroring', 'inactive', 'abnormal',
              'shutdown', 'reinvestigating', 'queued']

    transitions = [
        {'trigger': 'mirror', 'source': 'unknown', 'dest': 'mirroring'},
        {'trigger': 'queue', 'source': 'unknown', 'dest': 'queued'},
        {'trigger': 'inactive', 'source': 'unknown', 'dest': 'inactive'},
        {'trigger': 'reinvestigate', 'source': 'known', 'dest': 'reinvestigating'},
        {'trigger': 'queue', 'source': 'known', 'dest': 'queued'},
        {'trigger': 'inactive', 'source': 'known', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'mirroring', 'dest': 'known'},
        {'trigger': 'abnormal', 'source': 'mirroring', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'mirroring', 'dest': 'inactive'},
        {'trigger': 'unknown', 'source': 'inactive', 'dest': 'unknown'},
        {'trigger': 'shutdown', 'source': 'abnormal', 'dest': 'shutdown'},
        {'trigger': 'reinvestigate', 'source': 'abnormal', 'dest': 'reinvestigating'},
        {'trigger': 'queue', 'source': 'abnormal', 'dest': 'queued'},
        {'trigger': 'inactive', 'source': 'abnormal', 'dest': 'inactive'},
        {'trigger': 'known', 'source': 'reinvestigating', 'dest': 'known'},
        {'trigger': 'abnormal', 'source': 'reinvestigating', 'dest': 'abnormal'},
        {'trigger': 'inactive', 'source': 'reinvestigating', 'dest': 'inactive'},
        {'trigger': 'inactive', 'source': 'queued', 'dest': 'inactive'},
        {'trigger': 'mirror', 'source': 'queued', 'dest': 'mirroring'},
        {'trigger': 'reinvestigate', 'source': 'queued', 'dest': 'reinvestigating'},
        # must be pulled from database to get to these transitions
        {'trigger': 'unknown', 'source': 'mirroring', 'dest': 'unknown'},
        {'trigger': 'known', 'source': 'inactive', 'dest': 'known'},
        {'trigger': 'abnormal', 'source': 'inactive', 'dest': 'abnormal'},
        {'trigger': 'unknown', 'source': 'reinvestigating', 'dest': 'unknown'},
        {'trigger': 'unknown', 'source': 'queued', 'dest': 'unknown'},
        {'trigger': 'known', 'source': 'queued', 'dest': 'known'}
    ]

    def __init__(self, hashed_val):
        # Initialize the state machine
        self.machine = Machine(model=self, states=Endpoint.states,
                               transitions=Endpoint.transitions, initial='unknown')
        self.machine.name = hashed_val
