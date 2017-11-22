#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
Created on 21 Nov 2017
@author: dgrossman
'''


import hashlib
import json
import queue as Queue
from collections import defaultdict

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base
from poseidon.poseidonMonitor.endPoint import EndPoint
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import \
    BcfProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.faucet import \
    FaucetProxy

module_logger = Logger


class Endpoint_Wrapper():
    def __init__(self):
        self.state = defaultdict(EndPoint)
        self.logger = module_logger.logger

    def set(self, ep):
        self.state[ep.make_hash()] = ep

    def get_endpoint_state(self, my_hash):
        ''' return the state associated with a hash '''
        if my_hash in self.state:
            return self.state[my_hash].state
        return None

    def get_endpoint_next(self, my_hash):
        ''' return the next_state associated with a hash '''
        if my_hash in self.state:
            return self.state[my_hash].next_state
        return None

    def get_endpoint_ip(self, my_hash):
        ''' return the ip address associated with a hash '''
        if my_hash in self.state:
            return self.state[my_hash].endpoint_data['ip-address']
        return None

    def change_endpoint_state(self, my_hash, new_state=None):
        ''' update the state of an endpoint '''
        self.state[my_hash].state = new_state or self.state[my_hash].next_state
        self.state[my_hash].next_state = 'NONE'

    def change_endpoint_nextstate(self, my_hash, next_state):
        ''' updaate the next state of an endpoint '''
        self.state[my_hash].next_state = next_state

    def print_endpoint_state(self):
        ''' debug output about what the current state of endpoints is '''
        def same_old(logger, state, letter, endpoint_states):
            logger.info('*******{0}*********'.format(state))

            out_flag = False
            for my_hash in endpoint_states.keys():
                endpoint = endpoint_states[my_hash]
                if endpoint.state == state:
                    out_flag = True
                    logger.info('{0}:{1}:{2}->{3}:{4}'.format(letter,
                                                              my_hash,
                                                              endpoint.state,
                                                              endpoint.next_state,
                                                              endpoint.endpoint_data))
            if not out_flag:
                logger.info('None')

        states = [('K', 'KNOWN'), ('U', 'UNKNOWN'), ('M', 'MIRRORING'),
                  ('S', 'SHUTDOWN'), ('R', 'REINVESTIGATING')]

        self.logger.info('====START')
        for l, s in states:
            same_old(self.logger, s, l, self.state)

        self.logger.info('****************')
        self.logger.info('====STOP')
