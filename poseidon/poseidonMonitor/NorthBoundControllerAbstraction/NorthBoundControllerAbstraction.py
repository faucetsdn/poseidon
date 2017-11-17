#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
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
Created on 17 May 2016
@author: dgrossman
'''
import hashlib
import json
import queue as Queue
from collections import defaultdict

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import \
    BcfProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.faucet import \
    FaucetProxy

module_logger = Logger


class NorthBoundControllerAbstraction(Monitor_Action_Base):
    ''' handle abstracting poseidon from the controllers '''

    def __init__(self):
        super(NorthBoundControllerAbstraction, self).__init__()
        self.logger = module_logger.logger
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name


class Update_Switch_State(Monitor_Helper_Base):
    ''' handle periodic process, determine if switch state updated '''

    def __init__(self):
        super(Update_Switch_State, self).__init__()
        self.logger = module_logger.logger
        self.mod_name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None
        self.controller = {}
        self.controller['URI'] = None
        self.controller['USER'] = None
        self.controller['PASS'] = None
        self.controller['TYPE'] = None
        self.sdnc = None
        self.first_time = True
        self.endpoint_states = defaultdict(dict)
        self.m_queue = Queue.Queue()

    def return_endpoint_state(self):
        ''' give access to the endpoint_states '''
        return self.endpoint_states

    def first_run(self):
        ''' do some pre-run setup/configuration '''
        if self.configured:
            self.controller['TYPE'] = str(
                self.mod_configuration['controller_type'])
            if self.controller['TYPE'] == 'bcf':
                self.controller['URI'] = str(
                    self.mod_configuration['controller_uri'])
                self.controller['USER'] = str(
                    self.mod_configuration['controller_user'])
                self.controller['PASS'] = str(
                    self.mod_configuration['controller_pass'])

                myauth = {}
                myauth['password'] = self.controller['PASS']
                myauth['user'] = self.controller['USER']
                try:
                    self.sdnc = BcfProxy(self.controller['URI'], auth=myauth)
                except BaseException:
                    self.logger.error(
                        'BcfProxy could not connect to {0}'.format(
                            self.controller['URI']))
            elif self.controller['TYPE'] == 'faucet':
                try:
                    self.sdnc = FaucetProxy()
                except BaseException:
                    self.logger.error(
                        'FaucetProxy could not connect to {0}'.format(
                            self.controller['URI']))
            else:
                self.logger.error(
                    'Unknown SDN controller type {0}'.format(
                        self.controller['TYPE']))
        else:
            pass

    @staticmethod
    def make_hash(item):
        ''' hash the metadata in a sane way '''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        # nodhcp -> dhcp withname makes different hashes
        # {u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': None, u'ip-address': u'10.179.0.100'}}^
        # {u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': u'demo-laptop', u'ip-address': u'10.179.0.100'}}
        # ^^^ make different hashes if name is included
        # for word in ['tenant', 'mac', 'segment', 'name', 'ip-address']:

        for word in ['tenant', 'mac', 'segment', 'ip-address']:
            pre_h = pre_h + str(item.get(str(word), 'missing'))
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h

    def get_endpoint_state(self, my_hash):
        ''' return the state associated with a hash '''
        if my_hash in self.endpoint_states:
            return self.endpoint_states[my_hash]['state']
        return None

    def get_endpoint_next(self, my_hash):
        ''' return the next_state associated with a hash '''
        if my_hash in self.endpoint_states:
            return self.endpoint_states[my_hash]['next-state']
        return None

    def get_endpoint_ip(self, my_hash):
        ''' return the ip address associated with a hash '''
        if my_hash in self.endpoint_states:
            return self.endpoint_states[my_hash]['endpoint']['ip-address']
        return None

    def shutdown_endpoint(self, my_hash):
        ''' tell the controller to shutdown an endpoint by hash '''
        if my_hash in self.endpoint_states:
            my_ip = self.get_endpoint_ip(my_hash)
            next_state = self.get_endpoint_next(my_hash)
            self.sdnc.shutdown_ip(my_ip)
            self.change_endpoint_state(my_hash)
            self.logger.debug(
                'endpoint:{0}:{1}:{2}'.format(my_hash, my_ip, next_state))
            return True
        return False

    def mirror_endpoint(self, my_hash):
        ''' tell the controller to begin mirroring traffic '''
        if my_hash in self.endpoint_states:
            my_ip = self.get_endpoint_ip(my_hash)
            next_state = self.get_endpoint_next(my_hash)
            self.sdnc.mirror_ip(my_ip)
            self.change_endpoint_state(my_hash)
            self.logger.debug(
                'endpoint:{0}:{1}:{2}'.format(my_hash, my_ip, next_state))
            return True
        return False

    def unmirror_endpoint(self, my_hash):
        ''' tell the controller to unmirror traffic '''
        if my_hash in self.endpoint_states:
            my_ip = self.get_endpoint_ip(my_hash)
            next_state = self.get_endpoint_next(my_hash)
            self.sdnc.unmirror_ip(my_ip)
            self.logger.debug(
                'endpoint:{0}:{1}:{2}'.format(my_hash, my_ip, next_state))
            return True
        return False

    def make_endpoint_dict(self, my_hash, state, data):
        ''' make a new endpoint '''
        self.endpoint_states[my_hash]['state'] = state
        self.endpoint_states[my_hash]['next-state'] = 'NONE'
        self.endpoint_states[my_hash]['endpoint'] = data

    def change_endpoint_state(self, my_hash, new_state=None):
        ''' update the state of an endpoint '''
        self.endpoint_states[my_hash][
            'state'] = new_state or self.endpoint_states[my_hash]['next-state']
        self.endpoint_states[my_hash]['next-state'] = 'NONE'

    def change_endpoint_nextstate(self, my_hash, next_state):
        ''' updaate the next state of an endpoint '''
        self.endpoint_states[my_hash]['next-state'] = next_state

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        if self.first_time:
            self.first_time = False
            # TODO db call to see if really need to run things
            for machine in machines:
                h = self.make_hash(machine)
                self.logger.debug(
                    'adding address to known systems {0}'.format(machine))
                self.make_endpoint_dict(h, 'KNOWN', machine)
        else:
            for machine in machines:
                h = self.make_hash(machine)
                if h not in self.endpoint_states:
                    self.logger.debug(
                        '***** detected new address {0}'.format(machine))
                    self.make_endpoint_dict(h, 'UNKNOWN', machine)

    def print_endpoint_state(self):
        ''' debug output about what the current state of endpoints is '''
        def same_old(logger, state, letter, endpoint_states):
            logger.info('*******{0}*********'.format(state))

            out_flag = False
            for my_hash in endpoint_states.keys():
                my_dict = endpoint_states[my_hash]
                if my_dict['state'] == state:
                    out_flag = True
                    logger.info('{0}:{1}:{2}->{3}:{4}'.format(letter,
                                                              my_hash,
                                                              my_dict['state'],
                                                              my_dict['next-state'],
                                                              my_dict['endpoint']))
            if not out_flag:
                logger.info('None')

        states = [('K', 'KNOWN'), ('U', 'UNKNOWN'), ('M', 'MIRRORING'),
                  ('S', 'SHUTDOWN'), ('R', 'REINVESTIGATING')]

        self.logger.info('====START')
        for l, s in states:
            same_old(self.logger, s, l, self.endpoint_states)

        self.logger.info('****************')
        self.logger.info('====STOP')

    def update_endpoint_state(self):
        '''Handles Get requests'''
        self.retval['service'] = self.owner.mod_name + ':' + self.mod_name
        self.retval['times'] = self.times
        self.retval['machines'] = None
        self.retval['resp'] = 'bad'

        current = None
        parsed = None
        machines = {}

        try:
            current = self.sdnc.get_endpoints()
            parsed = self.sdnc.format_endpoints(current)
            machines = parsed
        except BaseException:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to {0}.'.format(
                    self.controller['URI']))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.logger.debug('MACHINES:{0}'.format(machines))
        self.find_new_machines(machines)

        self.print_endpoint_state()

        self.retval['machines'] = parsed
        self.retval['resp'] = 'ok'

        self.times = self.times + 1

        self.logger.info("MACHIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIINES:" + str(machines))
        return json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Update_Switch_State', Update_Switch_State)
