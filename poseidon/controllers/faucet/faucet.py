# -*- coding: utf-8 -*-
'''
Created on 17 November 2017
@author: Charlie Lewis
'''
import ipaddress
import json
import logging

from poseidon.controllers.faucet.connection import Connection
from poseidon.controllers.faucet.parser import Parser
from poseidon.volos.coprocessor import Coprocessor
from poseidon.volos.volos import Volos


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

        # parse volos config
        self.volos = Volos(controller)
        self.coprocessor = Coprocessor(controller)
        ignore_vlans = controller['ignore_vlans']
        if isinstance(ignore_vlans, str):
            self.ignore_vlans = json.loads(ignore_vlans)
        else:
            self.ignore_vlans = ignore_vlans
        ignore_ports = controller['ignore_ports']
        if isinstance(ignore_ports, str):
            self.ignore_ports = json.loads(ignore_ports)
        else:
            self.ignore_ports = ignore_ports
        trunk_ports = controller['trunk_ports']
        if isinstance(trunk_ports, str):
            self.trunk_ports = json.loads(trunk_ports)
        else:
            self.trunk_ports = trunk_ports
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
            self.log(self.log_file)
        for mac in self.mac_table:
            if self.learn_pub_adds:
                retval.append(self.mac_table[mac])
            else:
                # only allow private addresses
                if 'ip-address' in self.mac_table[mac][0] and (self.mac_table[mac][0]['ip-address'] == 'None' or
                                                               self.mac_table[mac][0]['ip-address'] is None or
                                                               not ipaddress.ip_address(self.mac_table[mac][0]['ip-address']).is_global):
                    retval.append(self.mac_table[mac])
        return retval

    def update_acls(self, rules_file=None, endpoints=None, force_apply_rules=None, force_remove_rules=None):
        self.logger.debug('updating acls')
        if self.host:
            self.receive_file('config')
            if self.config(self.config_file, 'apply_acls', None, None,
                           rules_file=rules_file, endpoints=endpoints,
                           force_apply_rules=force_apply_rules,
                           force_remove_rules=force_remove_rules):
                self.send_file('config')
        else:
            self.config(self.config_file, 'apply_acls', None, None,
                        rules_file=rules_file, endpoints=endpoints,
                        force_apply_rules=force_apply_rules,
                        force_remove_rules=force_remove_rules)
        # TODO check if config was successfully updated
        return True

    def shutdown_ip(self, ip_addr, shutdown=True, mac_addr=None):
        shutdowns = []
        port = 0
        switch = None
        if self.host:
            self.receive_file('config')
            if self.config(self.config_file,
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
            if self.config(self.config_file,
                           'shutdown', int(port), switch):
                self.send_file('config')
        else:
            self.config(self.config_file, 'shutdown', int(port), switch)
        # TODO check if config was successfully updated

    def mirror_mac(self, my_mac, my_switch, my_port):
        self.logger.debug('mirroring mac')
        port = None
        switch = None
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if port and switch:
            if self.host:
                self.receive_file('config')
                if self.config(self.config_file,
                               'mirror', int(port), switch):
                    self.send_file('config')
                    # TODO check if this is actually True
            else:
                self.config(self.config_file, 'mirror', int(port), switch)
        return True

    def unmirror_mac(self, my_mac, my_switch, my_port):
        port = 0
        switch = None
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if port and switch:
            trunk = False
            for sw in self.trunk_ports:
                if sw == switch and self.trunk_ports[sw].split(',')[1] == str(port):
                    trunk = True
            if not trunk:
                if self.host:
                    self.receive_file('config')
                    if self.config(self.config_file,
                                   'unmirror', int(port), switch):
                        self.send_file('config')
                        # TODO check if config was successfully updated
                else:
                    self.config(self.config_file, 'unmirror',
                                int(port), switch)
            else:
                self.logger.debug('not unmirroring a trunk port')
                return False
        return True

    def coprocess_mac(self, my_mac):
        self.logger.debug('coprocess mac: {0}'.format(my_mac))
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if self.host:
            self.receive_file('config')
            if self.config(self.config_file,
                           'coprocess', int(port), switch):
                self.send_file('config')
                # TODO check if this is actually True
        else:
            self.config(self.config_file, 'coprocess', int(port), switch)
        return True

    def uncoprocess_mac(self, my_mac):
        self.logger.debug('uncoprocess mac: {0}'.format(my_mac))
        port = 0
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']

                if self.host:
                    self.receive_file('config')
                    if self.config(self.config_file,
                                   'uncoprocess', int(port), switch):
                        self.send_file('config')
                        # TODO check if config was successfully updated
                else:
                    self.config(self.config_file, 'uncoprocess',
                                int(port), switch)
        return True
