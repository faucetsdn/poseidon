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
import json
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
                 learn_pub_adds=None,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        super(FaucetProxy, self).__init__(host,
                                          user,
                                          pw,
                                          config_file,
                                          log_file,
                                          mirror_ports,
                                          rabbit_enabled,
                                          learn_pub_adds,
                                          *args,
                                          **kwargs)
        if isinstance(mirror_ports, str):
            self.mirror_ports = json.loads(mirror_ports)
        else:
            self.mirror_ports = mirror_ports
        self.rabbit_enabled = rabbit_enabled
        self.learn_pub_adds = learn_pub_adds
        self.mac_table = {}

    @staticmethod
    def format_endpoints(data):
        '''
        return only the information needed for the application
        '''
        ret_list = list()
        for d in data:
            md = d[0]
            if 'ip-state' in md:
                del md['ip-state']
            md['name'] = None
            ret_list.append(md)
        return ret_list

    def get_endpoints(self, messages=None):
        retval = []

        if messages:
            module_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message or 'L2_EXPIRE' in message or 'PORT_CHANGE' in message:
                    module_logger.debug(
                        'l2 faucet message: {0}'.format(message))
                    self.event(message)
                else:
                    module_logger.debug('faucet event: {0}'.format(message))
        elif not self.rabbit_enabled:
            if self.host:
                self.receive_file('log')
                self.log(os.path.join(self.log_dir, 'faucet.log'))
            else:
                self.log(self.log_file)
        module_logger.debug('get_endpoints found:')
        for mac in self.mac_table:
            if (self.mac_table[mac][0]['ip-address'] != None and
                self.mac_table[mac][0]['ip-address'] != 'None' and
                self.mac_table[mac][0]['ip-address'] != '127.0.0.1' and
                self.mac_table[mac][0]['ip-address'] != '0.0.0.0' and
                self.mac_table[mac][0]['ip-address'] != '::' and
                not self.mac_table[mac][0]['ip-address'].startswith('169.254.') and
                    not self.mac_table[mac][0]['ip-address'].startswith('fe80:')):
                if not self.learn_pub_adds:
                    # only allow RFC 1918 ipv4 addresses and fd* ipv6 address
                    check_sec_octet = self.mac_table[mac][0]['ip-address'].split(
                        '.')
                    if len(check_sec_octet) > 1:
                        check_sec_octet = int(check_sec_octet[1])
                    if (self.mac_table[mac][0]['ip-address'].startswith('fd') or
                        self.mac_table[mac][0]['ip-address'].startswith('10.') or
                        self.mac_table[mac][0]['ip-address'].startswith('192.168.') or
                        (self.mac_table[mac][0]['ip-address'].startswith('172.') and
                         isinstance(check_sec_octet, int) and check_sec_octet > 15 and check_sec_octet < 32)):
                        module_logger.debug('{0}:{1}'.format(
                            mac, self.mac_table[mac]))
                        retval.append(self.mac_table[mac])
                else:
                    module_logger.debug('{0}:{1}'.format(
                        mac, self.mac_table[mac]))
                    retval.append(self.mac_table[mac])
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

    def mirror_ip(self, ip, messages=None):
        if messages:
            module_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    module_logger.debug(
                        'l2 faucet message: {0}'.format(message))
                    self.event(message)
        elif not self.rabbit_enabled:
            if self.host:
                self.receive_file('log')
                self.log(os.path.join(self.log_dir, 'faucet.log'))
            else:
                self.log(self.log_file)
        port = None
        switch = None
        status = None
        for mac in self.mac_table:
            if ip == self.mac_table[mac][0]['ip-address']:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if port and switch:
            if self.host:
                self.receive_file('config')
                if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                               'mirror', int(port), switch):
                    self.send_file('config')
                    # TODO check if this is actually True
                    status = True
            else:
                status = self.config(
                    self.config_file, 'mirror', int(port), switch)
        else:
            status = False
        module_logger.debug('mirror status: ' + str(status))
        # TODO check if config was successfully updated

    def unmirror_ip(self, ip, messages=None):
        if messages:
            module_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    module_logger.debug(
                        'l2 faucet message: {0}'.format(message))
                    self.event(message)
        elif not self.rabbit_enabled:
            if self.host:
                self.receive_file('log')
                self.log(os.path.join(self.log_dir, 'faucet.log'))
            else:
                self.log(self.log_file)
        port = 0
        switch = None
        status = None
        for mac in self.mac_table:
            if ip == self.mac_table[mac][0]['ip-address']:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if port and switch:
            if self.host:
                self.receive_file('config')
                if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                               'unmirror', int(port), switch):
                    self.send_file('config')
            else:
                status = self.config(
                    self.config_file, 'unmirror', int(port), switch)
        module_logger.debug('unmirror status: ' + str(status))
        # TODO check if config was successfully updated
