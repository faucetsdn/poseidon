#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
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
'''
Created on 17 November 2017
@author: cglewis
'''
from poseidon.baseClasses.Logger_Base import Logger

module_logger = Logger
module_logger = module_logger.logger


class FaucetProxy:

    def __init__(self):
        '''Initializes Faucet object.'''
        pass

    def format_endpoints(self):
        pass
    def get_endpoints(self):
        pass
    def get_switches(self):
        pass
    def get_tenants(self):
        pass
    def get_segments(self):
        pass
    def get_span_fabric(self):
        pass
    def get_byip(self):
        pass
    def get_bymac(self):
        pass
    def shutdown_ip(self):
        pass
    def shutdown_endpoint(self):
        pass
    def get_highest(self):
        pass
    def get_seq_by_ip(self):
        pass
    def mirror_ip(self):
        pass
    def unmirror_ip(self):
        pass
    def mirror_traffic(self):
        pass
