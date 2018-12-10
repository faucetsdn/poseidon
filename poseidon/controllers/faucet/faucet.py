# -*- coding: utf-8 -*-
'''
Created on 17 November 2017
@author: Charlie Lewis
'''
import json
import os

from poseidon.controllers.faucet.connection import Connection
from poseidon.controllers.faucet.parser import Parser
from poseidon.helpers.log import Logger


class FaucetProxy(Connection, Parser):

    def __init__(self,
                 controller,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        mirror_ports = controller['MIRROR_PORTS']
        if isinstance(mirror_ports, str):
            self.mirror_ports = json.loads(mirror_ports)
        else:
            self.mirror_ports = mirror_ports
        self.rabbit_enabled = controller['RABBIT_ENABLED']
        self.learn_pub_adds = controller['LEARN_PUBLIC_ADDRESSES']
        self.reinvestigation_frequency = controller['reinvestigation_frequency']
        self.max_concurrent_reinvestigations = controller['max_concurrent_reinvestigations']
        self.config_file = controller['CONFIG_FILE']
        self.log_file = controller['LOG_FILE']
        self.host = controller['URI']
        self.user = controller['USER']
        self.pw = controller['PASS']
        super(FaucetProxy, self).__init__(
            self.host,
            self.user,
            self.pw,
            self.config_file,
            self.log_file,
            self.mirror_ports,
            self.rabbit_enabled,
            self.learn_pub_adds,
            self.reinvestigation_frequency,
            self.max_concurrent_reinvestigations, *args, **kwargs)
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
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

    def check_connection(self):
        # TODO this should actually check if faucet is running (package or container)
        connected = False
        if self.host:
            self._connect()
            if self.ssh:
                connected = True
        else:  # faucet is running on the same host
            connected = True
        return connected

    def get_endpoints(self, messages=None):
        retval = []

        if messages:
            self.poseidon_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message or 'L2_EXPIRE' in message or 'PORT_CHANGE' in message:
                    self.poseidon_logger.debug(
                        'l2 faucet message: {0}'.format(message))
                    self.event(message)
                else:
                    self.poseidon_logger.debug(
                        'faucet event: {0}'.format(message))
        elif not self.rabbit_enabled:
            if self.host:
                self.receive_file('log')
                self.log(os.path.join(self.log_dir, 'faucet.log'))
            else:
                self.log(self.log_file)
        self.poseidon_logger.debug('get_endpoints found:')
        for mac in self.mac_table:
            if self.learn_pub_adds:
                self.poseidon_logger.debug('{0}:{1}'.format(
                    mac, self.mac_table[mac]))
                retval.append(self.mac_table[mac])
            else:
                # only allow RFC 1918 ipv4 addresses and fd* ipv6 address
                check_sec_octet = self.mac_table[mac][0]['ip-address'].split(
                    '.')
                if len(check_sec_octet) > 1:
                    check_sec_octet = int(check_sec_octet[1])
                if (self.mac_table[mac][0]['ip-address'] == 'None' or
                    self.mac_table[mac][0]['ip-address'] == None or
                    self.mac_table[mac][0]['ip-address'] == '::' or
                    self.mac_table[mac][0]['ip-address'] == '127.0.0.1' or
                    self.mac_table[mac][0]['ip-address'] == '0.0.0.0' or
                    self.mac_table[mac][0]['ip-address'].startswith('fe80::') or
                    self.mac_table[mac][0]['ip-address'].startswith('169.254.') or
                    self.mac_table[mac][0]['ip-address'].startswith('fd') or
                    self.mac_table[mac][0]['ip-address'].startswith('10.') or
                    self.mac_table[mac][0]['ip-address'].startswith('192.168.') or
                    (self.mac_table[mac][0]['ip-address'].startswith('172.') and
                     isinstance(check_sec_octet, int) and check_sec_octet > 15 and check_sec_octet < 32)):
                    self.poseidon_logger.debug('{0}:{1}'.format(
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

    def mirror_mac(self, my_mac, messages=None):
        self.poseidon_logger.info('mirroring mac')
        if messages:
            self.poseidon_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    self.poseidon_logger.debug(
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
            if my_mac == mac:
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
        self.poseidon_logger.info('mirror status: ' + str(status))
        # TODO check if config was successfully updated

    def unmirror_mac(self, my_mac, messages=None):
        if messages:
            self.poseidon_logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    self.poseidon_logger.debug(
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
            if my_mac == mac:
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
        self.poseidon_logger.debug('unmirror status: ' + str(status))
        # TODO check if config was successfully updated
