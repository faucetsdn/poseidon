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

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.basic.basicauth import BasicAuthControllerProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.mixins.jsonmixin import JsonMixin

module_logger = logging.getLogger(__name__)


class OnosProxy(JsonMixin, BasicAuthControllerProxy):

    def get_devices(self, devices_resource='devices'):
        """
        GET list of devices from the controller.
        """
        r = self.get_resource(devices_resource)
        return self.parse_json(r)

    def get_hosts(self, hosts_resource='hosts'):
        """
        GET list of hosts from the controller.
        """
        r = self.get_resource(hosts_resource)
        return self.parse_json(r)

    def get_flows(self, flows_resource='flows'):
        """
        GET list of flows from the controller.
        """
        r = self.get_resource(flows_resource)
        return self.parse_json(r)
