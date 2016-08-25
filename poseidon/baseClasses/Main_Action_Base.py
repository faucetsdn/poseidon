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
import logging

from poseidon.baseClasses.Rock_Bottom import Rock_Bottom

module_logger = logging.getLogger(__name__)


class Main_Action_Base(Rock_Bottom):  # pragma: no cover
    """ Basic call stubs

    Args:

    Attributes:
        actions (dict): dictionary of (string,instantiated class)
                        access for related classes
    """

    def __init__(self):
        super(Main_Action_Base, self).__init__()
        self.actions = dict()

    def set_owner(self, owner):
        """set parent class

        Args:
            owner: class be contacted when attempting to use other methods

        """
        self.owner = owner
        self.logger = module_logger
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner.mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        """get, parse, store configuration internally as dict """
        if self.owner:
            self.mod_configuration = dict()
            conf = self.owner.Config.get_section(self.config_section_name)
            if conf is not None:
                for item in conf:
                    k, v = item
                    self.mod_configuration[k] = v
                self.configured = True

    def first_run(self):
        """do any special setup after configure"""
        pass

    def configure_endpoints(self):
        """call stored classes setups and first_runs"""
        if self.owner and self.configured:
            for k, v in self.actions.iteritems():
                v.configure()
                v.first_run()

    def add_endpoint(self, name, handler):
        """hold a class in a dict

        Args:
            name:str    name of the class to hold
            handler:    instantiated class to hold
        """
        a = handler()
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
        """search and return managed class

        Args:
            name: name of class to mangage
        """
        if name in self.actions:
            return self.actions.get(name)
        else:
            return None
