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
import json
import logging

import requests

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base

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
        self.controller['ip'] = None
        self.controller['port'] = None
        self.controller['url'] = None

    def first_run(self):
        if self.configured:
            self.controller['ip'] = str(
                self.mod_configuration['controller_ip'])
            self.controller['port'] = str(
                self.mod_configuration['controller_port'])
            self.controller['url'] = 'http://' + self.controller['ip'] + \
                ':' + self.controller['port'] + '/v1/mock_controller/poll'
        else:
            pass

    def on_get(self, req, resp):
        """Haneles Get requests"""
        # TODO MSG NBCA to get switch state
        # TODO compare to previous switch state
        # TODO schedule something to occur for updated flows
        self.retval['service'] = self.owner.mod_name + ':' + self.mod_name
        self.retval['times'] = self.times
        # TODO change response to something reflecting success of traversal
        self.retval['resp'] = 'ok'

        try:
            controller_resp = requests.get(self.controller['url'])
            self.retval['controller'] = controller_resp.text
        except:
            self.logger.error(
                'Could not establish connection to {0}.'.format(self.controller['url']))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['url'])

        self.times = self.times + 1
        resp.body = json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Handle_Periodic', Handle_Periodic)
controller_interface.add_endpoint('Handle_Resource', Handle_Resource)
