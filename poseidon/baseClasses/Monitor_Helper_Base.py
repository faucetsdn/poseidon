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


class Monitor_Helper_Base(object):  # pragma: no cover
    """base class for the helper objets"""

    def __init__(self):
        self.mod_name = None
        self.owner = None
        self.config = None
        self.configured = False
        self.config_section_name = None

    def set_owner(self, owner):
        self.owner = owner
        if self.owner.mod_name is not None:
            self.config_section_name = self.owner.mod_name + ':' + self.mod_name
        else:
            self.config_section_name = 'None:' + self.mod_name

    def configure(self):
        # local valid
        if not self.owner:
            return
        # monitor valid
        if not self.owner.owner:
            return
        conf = self.owner.owner.Config.get_endpoint('Handle_SectionConfig')
        self.config = conf.direct_get(self.config_section_name)
        self.configured = True

    def on_post(self, req, resp):
        pass

    def on_put(self, req, resp, name):
        pass

    def on_get(self, req, resp):
        pass

    def on_delete(self, req, resp):
        pass
