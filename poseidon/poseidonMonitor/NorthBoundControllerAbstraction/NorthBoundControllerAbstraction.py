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
import requests

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base


class NorthBoundControllerAbstraction(Monitor_Action_Base):

    def __init__(self):
        super(NorthBoundControllerAbstraction, self).__init__()
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name


class Handle_Resource(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Resource, self).__init__()
        self.mod_name = self.__class__.__name__

    def on_get(self, req, resp, resource):
        resp.content_type = 'text/text'
        try:
            resp.body = self.mod_name + ' found: %s' % (resource)
        except:  # pragma: no cover
            pass


class Handle_Periodic(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Periodic, self).__init__()
        self.mod_name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None

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
            ip = self.owner.owner.Config.get_endpoint('Handle_FieldConfig').direct_get('controller_ip', 'NorthBoundControllerAbstraction:Handle_Periodic')
            port = self.owner.owner.Config.get_endpoint('Handle_FieldConfig').direct_get('controller_port', 'NorthBoundControllerAbstraction:Handle_Periodic')
            url = 'http://' + ip + ':' + port + '/v1/mock_controller/poll'
            controller_resp = requests.get(url)
            self.retval['controller'] = controller_resp.text
        except:
            self.retval['controller'] = 'Could not establish connection to controller.'

        self.times = self.times + 1
        resp.body = json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Handle_Periodic', Handle_Periodic)
controller_interface.add_endpoint('Handle_Resource', Handle_Resource)
