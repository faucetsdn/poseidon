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
Created on 14 Jul 2016
@author: dgrossman
"""
import logging

from poseidon.baseClasses.Rock_Bottom import Rock_Bottom

module_logger = logging.getLogger('baseClasses.Monitor_Action_base')

""" Base call stubs

Args:

Attributes:
actions (dict) : dictionary of (string,instantiated class)
                 access for thte related classes
"""


class Monitor_Action_Base(Rock_Bottom):  # pragma: no cover

    def __init__(self):
        super(Monitor_Action_Base, self).__init__()
        self.actions = dict()

    def set_owner(self, owner):
        """set parent class

        Args:
            owner: class to be contacted when attemptinto use other methods
        """

        self.owner = owner
        self.logger = module_logger
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner.mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        """get, parse, store configuration internally as dict """
        print self.__class__.__name__, 'Base:configure'
        if self.owner:
            print self.__class__.__name__, 'configure:owner'
            self.mod_configuration = dict()
            conf = self.owner.Config.get_endpoint('Handle_SectionConfig')
            if conf is not None:
                for item in conf.direct_get(self.mod_name):
                    k, v = item
                    self.mod_configuration[k] = v
                print '%s,%s:%s' % (self.__class__.__name__,
                                    self.mod_name,
                                    self.mod_configuration)
                self.configured = True

    def first_run(self):
        """do any special setup after the configure"""
        pass

    def configure_endpoints(self):
        """call stored classes setups and first runs"""
        # print self.mod_name,'configure_endpoints'
        if self.owner and self.configured:
            for k, v in self.actions.iteritems():
                print 'about to configure %s\n' % (k)
                v.configure()
                v.first_run()

    def add_endpoint(self, name, handler):
        """hosd a class in a dict

        Args:
            name:str    name of the class to hold
            handler:    instantiated class to hold
        """
        a = handler()
        # print name,handler
        a.set_owner(self)
        self.actions[name] = a

    def del_endpoint(self, name):
        """remove a managed class

        Args:
            name: name of the class to remove
        """
        if name in self.actions:
            self.actions.pop(name)

    def get_endpoint(self, name):
        """get a managed class

        Args:
            name: name of the class to get
        """
        if name in self.actions:
            return self.actions.get(name)
        else:
            return None
