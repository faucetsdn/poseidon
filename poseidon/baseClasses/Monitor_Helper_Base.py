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
Created on 14 July 2016
@author: dgrossman
"""
import logging

from poseidon.baseClasses.Rock_Bottom import Rock_Bottom


class Monitor_Helper_Base(Rock_Bottom):  # pragma: no cover
    """base class for the helper objets"""

    def __init__(self):
        super(Monitor_Helper_Base, self).__init__()

    def set_owner(self, owner):
        """set the parent class

        Args:
            owner: class to be contacted to use other methods
        """

        if owner.logger is not None:
            self.logger = owner.logger
        else:
            self.logger = logging.getLogger(__name__)

        self.logger.debug('set_owner = %s' % (owner.mod_name))
        self.owner = owner
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner .mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        """get, parse, store configuration internally as dict"""
        print self.mod_name, 'configure()'
        # local valid
        if not self.owner:
            print self.mod_name, 'ownerNull'
            return
        # monitor valid
        if not self.owner.owner:
            print self.mod_name, 'monitorNull'
            return
        self.mod_configuration = dict()
        conf = self.owner.owner.Config.get_endpoint('Handle_SectionConfig')
        if conf is not None:
            for item in conf.direct_get(self.config_section_name):
                k, v = item
                self.mod_configuration[k] = v
            print 'config:', self.config_section_name, ':', self.mod_configuration
            self.configured = True

    def first_run(self):
        """do special setup after configure"""
        pass

    def on_post(self, req, resp):
        """handle jrandom rest case"""
        pass

    def on_put(self, req, resp, name):
        """handle jrandom rest case"""
        pass

    def on_get(self, req, resp):
        """handle jrandom rest case"""
        pass

    def on_delete(self, req, resp):
        """handle jrandom rest case"""
        pass
