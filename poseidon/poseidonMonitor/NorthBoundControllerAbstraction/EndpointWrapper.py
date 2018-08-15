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
import json
from collections import defaultdict

import requests

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.Config.Config import config_interface
from poseidon.poseidonMonitor.endPoint import EndPoint


class Endpoint_Wrapper():
    def __init__(self):
        super(Endpoint_Wrapper, self).__init__()
        self.state = defaultdict(EndPoint)
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.mod_configuration = dict()
        self.mod_name = self.__class__.__name__
        self.Config = config_interface
        self.configSelf()

    def configSelf(self):
        ''' get configuraiton for this module '''
        conf = self.Config.get_endpoint('Handle_SectionConfig')
        for item in conf.direct_get(self.mod_name):
            k, v = item
            self.mod_configuration[k] = v
        ostr = '{0}:config:{1}'.format(self.mod_name, self.mod_configuration)
        self.poseidon_logger.debug(ostr)

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

    def update_vent_collector(self, my_hash, endpoint):
        ''' update the metadata on the endpoint's vent collector '''
        payload = {'id': my_hash,
                   'metadata': endpoint.to_str()}

        self.poseidon_logger.debug('vent update payload: ' + str(payload))

        vent_addr = self.mod_configuration['vent_ip'] + \
            ':' + self.mod_configuration['vent_port']
        uri = 'http://' + vent_addr + '/update'

        try:
            resp = requests.post(uri, data=json.dumps(payload))
            self.poseidon_logger.debug(
                'collector update response: ' + resp.text)
        except Exception as e:  # pragma: no cover
            self.logger.error('failed to update vent collector' + str(e))

    def print_endpoint_state(self):
        ''' debug output about what the current state of endpoints is '''
        def same_old(state, letter):
            self.poseidon_logger.info('*******{0}*********'.format(state))

            out_flag = False
            e_states = self.state.copy()
            for my_hash in e_states.keys():
                endpoint = e_states[my_hash]
                if endpoint.state == state:
                    if 'active' in endpoint.endpoint_data and endpoint.endpoint_data['active'] == 0:
                        endpoint.prev_state = endpoint.state
                        endpoint.state = 'UNKNOWN'
                        endpoint.next_state = 'REINVESTIGATING'
                    else:
                        out_flag = True
                        pp_endpoint_data = endpoint.endpoint_data.copy()
                        del pp_endpoint_data['active']
                        del pp_endpoint_data['name']
                        pp_endpoint_data['ip'] = pp_endpoint_data['ip-address']
                        del pp_endpoint_data['ip-address']
                        pp_endpoint_data['s'] = pp_endpoint_data['segment']
                        del pp_endpoint_data['segment']
                        pp_endpoint_data['p'] = pp_endpoint_data['port']
                        del pp_endpoint_data['port']
                        pp_endpoint_data['v'] = pp_endpoint_data['tenant']
                        del pp_endpoint_data['tenant']
                        self.poseidon_logger.info('{0}:{1}:{2}->{3}:{4}'.format(letter,
                                                                                my_hash,
                                                                                endpoint.state,
                                                                                endpoint.next_state,
                                                                                pp_endpoint_data))
                    # update metadata on vent collectors
                    self.update_vent_collector(my_hash, endpoint)
            if not out_flag:
                self.poseidon_logger.info('None')

        states = [('K', 'KNOWN'), ('U', 'UNKNOWN'), ('M', 'MIRRORING'),
                  ('S', 'SHUTDOWN'), ('R', 'REINVESTIGATING')]

        self.poseidon_logger.info('====START')
        for l, s in states:
            same_old(s, l)

        self.poseidon_logger.info('****************')
        self.poseidon_logger.info('====STOP')

        # cleanup endpoints that are no longer active
        hashes = self.state.copy()
        for my_hash in hashes:
            if self.state[my_hash].endpoint_data['active'] == 0:
                del self.state[my_hash]
