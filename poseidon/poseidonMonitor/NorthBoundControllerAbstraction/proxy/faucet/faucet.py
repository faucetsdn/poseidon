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
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.connection import \
    Connection
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.parser import \
    Parser

module_logger = Logger.logger


class FaucetProxy(Connection, Parser):

    def __init__(self,
                 host,
                 user=None,
                 pw=None,
                 config_file=None,
                 log_file=None,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        super(FaucetProxy, self).__init__(host,
                                          user,
                                          pw,
                                          config_file,
                                          log_file,
                                          *args,
                                          **kwargs)

    @staticmethod
    def format_endpoints(data):
        '''
        return only the information needed for the application
        '''
        ret_list = list()
        for d in data:
            md = d[0]
            del md['ip-state']
            md['name'] = None
            ret_list.append(md)
        return ret_list

    def get_endpoints(self):
        self.receive_file('log')
        retval = []

        # NOTE very fragile, prone to errors
        mac_table = {}
        with open('/tmp/faucet.log', 'r') as f:
            for line in f:
                if 'L2 learned' in line:
                    learned_mac = line.split()
                    data = {'ip-address': learned_mac[16][0:-1],
                            'ip-state': 'L2 learned',
                            'mac': learned_mac[10],
                            'segment': learned_mac[7][1:-1],
                            'tenant': learned_mac[21] + learned_mac[22]}
                    if learned_mac[10] in mac_table:
                        dup = False
                        for d in mac_table[learned_mac[10]]:
                            if data == d:
                                dup = True
                        if dup:
                            mac_table[learned_mac[10]].remove(data)
                        mac_table[learned_mac[10]].insert(0, data)
                    else:
                        mac_table[learned_mac[10]] = [data]
        module_logger.debug('get_endpoints found:')
        for mac in mac_table:
            module_logger.debug('{0}:{1}'.format(
                mac, mac_table[mac]))
            retval.append(mac_table[mac])
        return retval

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
        self.config('/tmp/faucet.yaml')
        # TODO
        return shutdowns

    def shutdown_endpoint(self):
        self.config('/tmp/faucet.yaml')

    def get_highest(self):
        pass

    def get_seq_by_ip(self):
        pass

    def mirror_ip(self):
        self.config('/tmp/faucet.yaml')
        pass

    def unmirror_ip(self):
        self.config('/tmp/faucet.yaml')
        pass

    def mirror_traffic(self):
        self.config('/tmp/faucet.yaml')
        pass
