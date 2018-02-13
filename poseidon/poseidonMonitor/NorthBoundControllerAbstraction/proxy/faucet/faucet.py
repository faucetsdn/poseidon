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
import os

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.connection import \
    Connection
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.parser import \
    Parser

module_logger = Logger.logger


class FaucetProxy(Connection, Parser):

    def __init__(self,
                 host=None,
                 user=None,
                 pw=None,
                 config_file=None,
                 log_file=None,
                 mirror_ports=None,
                 rabbit_enabled=None,
                 rabbit_host=None,
                 rabbit_exchange=None,
                 rabbit_exchange_type=None,
                 rabbit_routing_key=None,
                 rabbit_port=None,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        super(FaucetProxy, self).__init__(host,
                                          user,
                                          pw,
                                          config_file,
                                          log_file,
                                          mirror_ports,
                                          rabbit_enabled=None,
                                          rabbit_host=None,
                                          rabbit_exchange=None,
                                          rabbit_exchange_type=None,
                                          rabbit_routing_key=None,
                                          rabbit_port=None,
                                          *args,
                                          **kwargs)
        self.mirror_ports = mirror_ports
        self.events()

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
        retval = []

        if self.host:
            self.receive_file('log')
            mac_table = self.log(os.path.join(self.log_dir, 'faucet.log'))
        else:
            mac_table = self.log(self.log_file)
        module_logger.debug('get_endpoints found:')
        for mac in mac_table:
            if (mac_table[mac][0]['ip-address'] != 'None' and
                mac_table[mac][0]['ip-address'] != '127.0.0.1' and
                mac_table[mac][0]['ip-address'] != '0.0.0.0' and
                mac_table[mac][0]['ip-address'] != '::' and
                not mac_table[mac][0]['ip-address'].startswith('fe80:')):
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
        port = 0
        switch = None
        if self.host:
            self.receive_file('config')
            if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                           'shutdown', int(port), switch):
                self.send_file('config')
        else:
            self.config(self.config_file, 'shutdown', int(port), switch)
        # TODO check if config was successfully updated
        return shutdowns

    def shutdown_endpoint(self):
        port = 0
        switch = None
        if self.host:
            self.receive_file('config')
            if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                           'shutdown', int(port), switch):
                self.send_file('config')
        else:
            self.config(self.config_file, 'shutdown', int(port), switch)
        # TODO check if config was successfully updated

    def get_highest(self):
        pass

    def get_seq_by_ip(self):
        pass

    def mirror_ip(self, ip):
        if self.host:
            self.receive_file('log')
            mac_table = self.log(os.path.join(self.log_dir, 'faucet.log'))
        else:
            mac_table = self.log(self.log_file)
        port = 0
        switch = None
        for mac in mac_table:
            if ip == mac_table[mac][0]['ip-address']:
                port = mac_table[mac][0]['port']
                switch = mac_table[mac][0]['segment']
        if port and switch:
            if self.host:
                self.receive_file('config')
                if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                               'mirror', int(port), switch):
                    self.send_file('config')
            else:
                self.config(self.config_file, 'mirror', int(port), switch)
        # TODO check if config was successfully updated

    def unmirror_ip(self, ip):
        port = 0
        switch = None
        if self.host:
            self.receive_file('config')
            if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                           'unmirror', int(port), switch):
                self.send_file('config')
        else:
            self.config(self.config_file, 'unmirror', int(port), switch)
        # TODO check if config was successfully updated

    def mirror_traffic(self):
        port = 0
        switch = None
        if self.host:
            self.receive_file('config')
            if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                           'mirror', int(port), switch):
                self.send_file('config')
        else:
            self.config(self.config_file, 'mirror', int(port), switch)
        # TODO check if config was successfully updated
