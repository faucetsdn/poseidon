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
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.connection import Connection

module_logger = Logger.logger


class FaucetProxy(Connection):

    def __init__(self, host, user=None, pw=None, *args, **kwargs):
        '''Initializes Faucet object.'''
        super(FaucetProxy, self).__init__(host, user, pw, *args, **kwargs)

    @staticmethod
    def format_endpoints(data):
        '''
        return only the information needed for the application
        '''
        ret_list = list()
        # TODO
        return []

    def get_endpoints(self):
        pass

    def get_switches(self):
        pass

    def get_ports(self):
        pass

    def get_vlans(self):
        pass

    def get_span_fabric(self):
        pass

    def get_byip(self, ipaddr):
        '''
        return records about ip addresses from get_endpoints
        to be used by shutdown_ip
        '''
        endpoints = self.get_endpoints()
        match_list = []
        # TODO
        return match_list

    def get_bymac(self, mac_addr):
        '''
        return records about mac address from get_endpoints
        '''
        endpoints = self.get_endpoints()
        match_list = []
        # TODO
        return match_list

    def shutdown_ip(self, ip_addr, shutdown=True, mac_addr=None):
        shutdowns = []
        # TODO
        return shutdowns

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
