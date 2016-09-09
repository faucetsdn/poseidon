#!/usr/bin/env python
#
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
"""
Created on 17 May 2016
@author: dgrossman
"""
import hashlib
import json
import logging

import requests

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import BcfProxy

logging.basicConfig()
module_logger = logging.getLogger(__name__)


class NorthBoundControllerAbstraction(Monitor_Action_Base):
    ''' handle abstracting poseidon from the controllers '''

    def __init__(self):
        super(NorthBoundControllerAbstraction, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name


class Handle_Resource(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Resource, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__

    def on_get(self, req, resp, resource):
        ''' handle reading endpoint '''
        resp.content_type = 'text/text'
        try:
            resp.body = self.mod_name + ' found: {0}'.format(resource)
        except:  # pragma: no cover
            pass


class Handle_Periodic(Monitor_Helper_Base):
    ''' handle periodic process, determine if switch state updated '''

    def __init__(self):
        super(Handle_Periodic, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None
        self.controller = {}
        self.controller['URI'] = None
        self.controller['USER'] = None
        self.controller['PASS'] = None
        self.bcf = None
        self.first_time = True
        self.prev_endpoints = {}
        self.new_endpoints = {}

    def first_run(self):
        if self.configured:
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
                self.bcf = BcfProxy(self.controller['URI'], auth=myauth)
            except:
                self.logger.error(
                    'BcfProxy coult not connect to {0}'.format(self.controller['URI']))
        else:
            pass

    @staticmethod
    def make_hash(item):
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        for word in ['tenant', 'mac', 'segment', 'name', 'ip-address']:
            pre_h = pre_h + str(item.get(str(word), 'missing'))
        h.update(pre_h)
        post_h = h.hexdigest()
        return post_h

    def on_get(self, req, resp):
        """Handles Get requests"""
        # TODO compare to previous switch state
        # TODO schedule something to occur for updated flows

        self.retval['service'] = self.owner.mod_name + ':' + self.mod_name
        self.retval['times'] = self.times
        self.retval['machines'] = None
        self.retval['resp'] = 'bad'

        current = None
        parsed = None

        try:
            current = self.bcf.get_endpoints()
            parsed = self.bcf.format_endpoints(current)
        except:
            self.logger.error(
                'Could not establish connection to {0}.'.format(self.controller['URI']))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        machines = parsed

        if self.first_time:
            self.first_time = False
            # @TODO db call to see if really need to run things
            for machine in machines:
                h = self.make_hash(machine)
                module_logger.critical(
                    'adding  address to known systems {0}'.format(machine))
                self.prev_endpoints[h] = machine
        else:
            for machine in machines:
                h = self.make_hash(machine)
                if h not in self.prev_endpoints:
                    module_logger.critical(
                        '***** detected new address {0}'.format(machine))
                    self.new_endpoints[h] = machine

        self.retval['machines'] = parsed
        self.retval['resp'] = 'ok'

        # TODO change response to something reflecting success of traversal

        self.times = self.times + 1
        resp.body = json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Handle_Periodic', Handle_Periodic)
controller_interface.add_endpoint('Handle_Resource', Handle_Resource)
