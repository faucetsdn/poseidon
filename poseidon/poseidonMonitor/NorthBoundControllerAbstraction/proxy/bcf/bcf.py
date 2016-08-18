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
Created on 25 July 2016
@author: kylez
"""
import logging

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.cookie.cookieauth import CookieAuthControllerProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.mixins.jsonmixin import JsonMixin

module_logger = logging.getLogger('poseidonMonitor.NBCA.proxy.bfc.bfc')


class BcfProxy(JsonMixin, CookieAuthControllerProxy):

    def get_endpoints(self, endpoints_resource='data/controller/applications/bcf/info/endpoint-manager/endpoint'):
        '''
        GET list of endpoints from the controller.
        '''
        r = self.get_resource(endpoints_resource)
        return self.parse_json(r)

    def get_switches(self, switches_resource='data/controller/applications/bcf/info/fabric/switch'):
        '''
        GET list of switches from the controller.
        '''
        r = self.get_resource(switches_resource)
        return self.parse_json(r)
