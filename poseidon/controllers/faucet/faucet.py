# -*- coding: utf-8 -*-
'''
Created on 17 November 2017
@author: Charlie Lewis
'''
import ipaddress
import json
import logging
import os

from poseidon.controllers.faucet.connection import Connection
from poseidon.controllers.faucet.parser import Parser


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
        self.ignore_vlans = controller['ignore_vlans']
        self.ignore_ports = controller['ignore_ports']
        self.trunk_ports = controller['trunk_ports']
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
            self.max_concurrent_reinvestigations,
            self.ignore_vlans,
            self.ignore_ports,
            self.trunk_ports, *args, **kwargs)
        self.logger = logging.getLogger('faucet')
        self.mac_table = {}
        Parser().clear_mirrors(self.config_file)

    @staticmethod
    def format_endpoints(data, controller):
        '''
        return only the information needed for the application
        '''
        ret_list = list()
        for d in data:
            md = d[0]
            d.reverse()
            for i, _ in enumerate(d):
                ipv4_set = False
                ipv6_set = False
                if 'ip-address' in d[i]:
                    if ':' in d[i]['ip-address']:
                        md['ipv6'] = d[i]['ip-address']
                        ipv6_set = True
                    else:
                        md['ipv4'] = d[i]['ip-address']
                        ipv4_set = True
                if 'ipv4' in md:
                    ipv4_set = True
                if 'ipv6' in md:
                    ipv6_set = True
            if not ipv4_set:
                md['ipv4'] = 0
            if not ipv6_set:
                md['ipv6'] = 0
            if 'ip-state' in md:
                del md['ip-state']
            if 'ip-address' in md:
                del md['ip-address']

            md['controller_type'] = 'faucet'
            md['controller'] = controller
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
            self.logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message or 'L2_EXPIRE' in message or 'PORT_CHANGE' in message:
                    self.logger.debug(
                        'l2 faucet message: {0}'.format(message))
                    self.event(message)
                else:
                    self.logger.debug(
                        'faucet event: {0}'.format(message))
        elif not self.rabbit_enabled:
            if self.host:
                self.receive_file('log')
                self.log(os.path.join(self.log_dir, 'faucet.log'))
            else:
                self.log(self.log_file)
        for mac in self.mac_table:
            if self.learn_pub_adds:
                retval.append(self.mac_table[mac])
            else:
                # only allow private addresses
                if 'ip-address' in self.mac_table[mac][0] and (self.mac_table[mac][0]['ip-address'] == 'None' or
                                                               self.mac_table[mac][0]['ip-address'] == None or
                                                               not ipaddress.ip_address(self.mac_table[mac][0]['ip-address']).is_global):
                    retval.append(self.mac_table[mac])
        return retval

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

    def mirror_mac(self, my_mac, my_switch, my_port, messages=None):
        self.logger.debug('mirroring mac')
        if messages:
            self.logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    self.logger.debug(
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
        self.logger.debug('mirror status: ' + str(status))
        return status

    def unmirror_mac(self, my_mac, my_switch, my_port, messages=None):
        if messages:
            self.logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if 'L2_LEARN' in message:
                    self.logger.debug(
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
            trunk = False
            for sw in self.trunk_ports:
                if sw == switch and self.trunk_ports[sw] == port:
                    trunk = True
            if not trunk:
                if self.host:
                    self.receive_file('config')
                    if self.config(os.path.join(self.config_dir, 'faucet.yaml'),
                                   'unmirror', int(port), switch):
                        self.send_file('config')
                        # TODO check if config was successfully updated
                        status = True
                else:
                    status = self.config(
                        self.config_file, 'unmirror', int(port), switch)
            else:
                self.logger.debug('not unmirroring a trunk port')
        self.logger.debug('unmirror status: ' + str(status))
        return status
