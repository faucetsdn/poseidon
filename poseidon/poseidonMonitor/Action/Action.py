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
import logging

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base


module_logger = logging.getLogger('poseidonMonitor.Action')


class Action(Monitor_Action_Base):
    """Poseidon Action Rest Interface"""

    def __init__(self):
        super(Action, self).__init__()
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name
        self.logger = module_logger


class Handle_Default(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Default, self).__init__()
        self.mod_name = self.__class__.__name__

    def on_get(self, req, resp, resource):
        resp.content_type = 'text/text'
        try:
            resp.body = self.mod_name + ' found: %s' % (resource)
        except:  # pragma: no cover
            resp.body = 'failed'


action_interface = Action()
action_interface.add_endpoint('Handle_Default', Handle_Default)
