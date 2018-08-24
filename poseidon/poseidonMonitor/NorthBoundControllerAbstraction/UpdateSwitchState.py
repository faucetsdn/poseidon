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
Created on 20 Nov 2017
@author: dgrossman
'''
import ast
import json

import queue as Queue

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base
from poseidon.poseidonMonitor.endPoint import EndPoint
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.EndpointWrapper import \
    Endpoint_Wrapper
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import \
    BcfProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.faucet import \
    FaucetProxy


class Update_Switch_State(Monitor_Helper_Base):
    ''' handle periodic process, determine if switch state updated '''

    def __init__(self):
        super(Update_Switch_State, self).__init__()
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.mod_name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None

        # settings for all controllers
        self.controller = {}
        self.controller['URI'] = None
        self.controller['USER'] = None
        self.controller['PASS'] = None
        self.controller['TYPE'] = None
        self.controller['SPAN_FABRIC_NAME'] = 'vent'
        self.controller['INTERFACE_GROUP'] = 'ig1'

        # settings for FAUCET
        self.controller['CONFIG_FILE'] = None
        self.controller['LOG_FILE'] = None
        self.controller['MIRROR_PORTS'] = None
        self.controller['RABBIT_ENABLED'] = False
        self.controller['LEARN_PUBLIC_ADDRESSES'] = False

        # set defaults
        self.reinvestigation_frequency = 900
        self.max_concurrent_reinvestigations = 2

        self.sdnc = None
        self.first_time = True
        self.endpoints = Endpoint_Wrapper()
        self.m_queue = Queue.Queue()

    def return_endpoint_state(self):
        ''' give access to the endpoint_states '''
        return self.endpoints

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

                if 'controller_span_fabric_name' in self.mod_configuration:
                    self.controller['SPAN_FABRIC_NAME'] = str(
                        self.mod_configuration['controller_span_fabric_name']
                    )

                if 'controller_interface_group' in self.mod_configuration:
                    self.controller['INTERFACE_GROUP'] = str(
                        self.mod_configuration['controller_interface_group']
                    )

                myauth = {}
                myauth['password'] = self.controller['PASS']
                myauth['user'] = self.controller['USER']
                try:
                    self.sdnc = BcfProxy(self.controller['URI'], auth=myauth, span_fabric_name=self.controller[
                                         'SPAN_FABRIC_NAME'], interface_group=self.controller['INTERFACE_GROUP'])
                except BaseException as e:  # pragma: no cover
                    self.logger.error(
                        'BcfProxy could not connect to {0} because {1}'.format(
                            self.controller['URI'], e))
            elif self.controller['TYPE'] == 'faucet':
                try:
                    if 'learn_public_addresses' in self.mod_configuration:
                        if self.mod_configuration['learn_public_addresses'] == 'Yes':
                            self.controller['LEARN_PUBLIC_ADDRESSES'] = True
                        else:
                            self.controller['LEARN_PUBLIC_ADDRESSES'] = False
                    if 'controller_uri' in self.mod_configuration:
                        self.controller['URI'] = str(
                            self.mod_configuration['controller_uri'])
                    if 'controller_user' in self.mod_configuration:
                        self.controller['USER'] = str(
                            self.mod_configuration['controller_user'])
                    if 'controller_pass' in self.mod_configuration:
                        self.controller['PASS'] = str(
                            self.mod_configuration['controller_pass'])
                    if 'controller_config_file' in self.mod_configuration:
                        self.controller['CONFIG_FILE'] = str(
                            self.mod_configuration['controller_config_file'])
                    if 'controller_log_file' in self.mod_configuration:
                        self.controller['LOG_FILE'] = str(
                            self.mod_configuration['controller_log_file'])
                    if 'controller_mirror_ports' in self.mod_configuration:
                        self.controller['MIRROR_PORTS'] = ast.literal_eval(
                            self.mod_configuration['controller_mirror_ports'])
                    if 'rabbit_enabled' in self.mod_configuration:
                        self.controller['RABBIT_ENABLED'] = ast.literal_eval(
                            self.mod_configuration['rabbit_enabled'])
                    self.sdnc = FaucetProxy(host=self.controller['URI'],
                                            user=self.controller['USER'],
                                            pw=self.controller['PASS'],
                                            config_file=self.controller['CONFIG_FILE'],
                                            log_file=self.controller['LOG_FILE'],
                                            mirror_ports=self.controller['MIRROR_PORTS'],
                                            rabbit_enabled=self.controller['RABBIT_ENABLED'],
                                            learn_pub_adds=self.controller['LEARN_PUBLIC_ADDRESSES'],
                                            reinvestigation_frequency=self.reinvestigation_frequency,
                                            max_concurrent_reinvestigations=self.max_concurrent_reinvestigations)
                except BaseException as e:  # pragma: no cover
                    self.logger.error(
                        'FaucetProxy could not connect to {0} because {1}'.format(
                            self.controller['URI'], e))
            else:
                self.logger.error(
                    'Unknown SDN controller type {0}'.format(
                        self.controller['TYPE']))

    def shutdown_endpoint(self, my_hash):
        ''' tell the controller to shutdown an endpoint by hash '''
        if my_hash in self.endpoints.state:
            my_ip = self.endpoints.get_endpoint_ip(my_hash)
            next_state = self.endpoints.get_endpoint_next(my_hash)
            self.sdnc.shutdown_ip(my_ip)
            self.endpoints.change_endpoint_state(my_hash)
            self.poseidon_logger.debug(
                'endpoint:{0}:{1}:{2}'.format(my_hash, my_ip, next_state))
            return True
        return False

    def mirror_endpoint(self, my_hash, messages=None):
        ''' tell the controller to begin mirroring traffic '''
        if my_hash in self.endpoints.state:
            my_mac = self.endpoints.get_endpoint_mac(my_hash)
            my_ip = self.endpoints.get_endpoint_ip(my_hash)
            next_state = self.endpoints.get_endpoint_next(my_hash)
            self.sdnc.mirror_mac(my_mac, messages=messages)
            self.endpoints.change_endpoint_state(my_hash)
            self.poseidon_logger.debug(
                'endpoint:{0}:{1}:{2}:{3}'.format(my_hash, my_mac, my_ip, next_state))
            return True
        return False

    def unmirror_endpoint(self, my_hash, messages=None):
        ''' tell the controller to unmirror traffic '''
        if my_hash in self.endpoints.state:
            my_mac = self.endpoints.get_endpoint_mac(my_hash)
            my_ip = self.endpoints.get_endpoint_ip(my_hash)
            next_state = self.endpoints.get_endpoint_next(my_hash)
            self.sdnc.unmirror_mac(my_mac, messages=messages)
            self.poseidon_logger.debug(
                'endpoint:{0}:{1}:{2}:{3}'.format(my_hash, my_mac, my_ip, next_state))
            return True
        return False

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        changed = False
        if self.first_time:
            self.first_time = False
            # TODO db call to see if really need to run things
            for machine in machines:
                end_point = EndPoint(machine, state='KNOWN')
                self.poseidon_logger.info(
                    'adding address to known systems {0}'.format(machine))
                self.endpoints.set(end_point)
            changed = True
        else:
            machine_hashes = []
            for machine in machines:
                end_point = EndPoint(machine, state='UNKNOWN')
                h = end_point.make_hash()
                ep = None
                if h in self.endpoints.state:
                    ep = self.endpoints.state[h]
                if end_point.endpoint_data['active'] == 1:
                    machine_hashes.append(h)

                    if h not in self.endpoints.state:
                        self.poseidon_logger.info(
                            '***** detected new address {0}'.format(machine))
                        self.endpoints.set(end_point)
                        changed = True
                elif ep is not None and end_point.endpoint_data['active'] != ep.endpoint_data['active']:
                    self.endpoints.set(end_point)
                    changed = True
        if changed:
            self.endpoints.print_endpoint_state()

    def update_endpoint_state(self, messages=None):
        '''Handles Get requests'''
        self.retval['service'] = self.owner.mod_name + ':' + self.mod_name
        self.retval['times'] = self.times
        self.retval['machines'] = None
        self.retval['resp'] = 'bad'

        current = None
        parsed = None
        machines = {}

        try:
            current = self.sdnc.get_endpoints(messages=messages)
            parsed = self.sdnc.format_endpoints(current)
            machines = parsed
        except BaseException as e:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to {0} because {1}.'.format(
                    self.controller['URI'], e))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.poseidon_logger.debug('MACHINES:{0}'.format(machines))
        self.find_new_machines(machines)

        self.retval['machines'] = parsed
        self.retval['resp'] = 'ok'

        self.times = self.times + 1

        return json.dumps(self.retval)
