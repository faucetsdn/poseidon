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

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base


class NorthBoundControllerAbstraction(Monitor_Action_Base):

    def __init__(self):
        super(NorthBoundControllerAbstraction, self).__init__()
        self.mod_Name = self.__class__.__name__
        self.owner = None
        self.actions = dict()

    def add_endpoint(self, name, handler):
        a = handler()
        a.owner = self
        self.actions[name] = a

    def del_endpoint(self, name):
        if name in self.actions:
            self.actions.pop(name)

    def get_endpoint(self, name):
        if name in self.actions:
            return self.actions.get(name)
        else:
            return None


class Handle_Resource(Monitor_Helper_Base):

    def __init__(self):
        self.mod_Name = self.__class__.__name__

    def on_get(self, req, resp, resource):
        resp.content_type = 'text/text'
        try:
            resp.body = self.mod_Name + ' found: %s' % (resource)
        except:  # pragma: no cover
            pass


class Handle_Periodic(Monitor_Helper_Base):

    def __init__(self):
        self.mod_Name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None

    def on_get(self, req, resp):
        """Haneles Get requests"""
        # TODO MSG NBCA to get switch state
        # TODO compare to previous switch state
        # TODO schedule something to occur for updated flows
        self.retval['service'] = self.owner.mod_Name + ':' + self.mod_Name
        self.retval['times'] = self.times
        # TODO change response to something reflecting success of traversal
        self.retval['resp'] = 'ok'
        self.times = self.times + 1
        resp.body = json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Handle_Periodic', Handle_Periodic)
controller_interface.add_endpoint('Handle_Resource', Handle_Resource)
