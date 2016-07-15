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
Created on  15 July 2016
@author: dgrossman
"""


class Main_Action_Base(object):  # pragma: no cover

    def __init__(self):
        self.mod_name = self.__class__.__name__
        self.owner = None
        self.mod_configuraiton = None
        self.configured = False
        self.config_section_name = None
        self.actions = dict()

    def set_owner(self, owner):
        self.owner = owner
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner.mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        if self.owner:
            self.mod_configuration = self.owner.Config.get_section(
                self.config_section_name)
            self.configured = True

    def configure_endpoints(self):
        if self.owner and self.configured:
            for k, v in self.actions.iteritems():
                v.configure()

    def add_endpoint(self, name, handler):
        a = handler()
        a.set_owner(self)
        self.actions[name] = a

    def del_endpoint(self, name):
        if name in self.actions:
            self.actions.pop(name)

    def get_endpoint(self, name):
        if name in self.actions:
            return self.actions.get(name)
        else:
            return None
