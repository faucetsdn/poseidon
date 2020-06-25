# -*- coding: utf-8 -*-
'''
Created on 17 November 2017
@author: Charlie Lewis
'''
import ipaddress
import json
import logging

from poseidon.controllers.faucet.parser import Parser
from poseidon.volos.coprocessor import Coprocessor
from poseidon.volos.volos import Volos


class FaucetProxy(Parser):

    def __init__(self,
                 controller,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        self.mirror_ports = controller['MIRROR_PORTS']
        self.tunnel_vlan = controller['tunnel_vlan']
        self.tunnel_name = controller['tunnel_name']
        self.learn_pub_adds = controller['LEARN_PUBLIC_ADDRESSES']
        self.reinvestigation_frequency = controller['reinvestigation_frequency']
        self.max_concurrent_reinvestigations = controller['max_concurrent_reinvestigations']
        self.config_file = controller['CONFIG_FILE']
        self.trunk_ports = controller['trunk_ports']
        self.ignore_vlans = controller['ignore_vlans']
        self.ignore_ports = controller['ignore_ports']

        for json_conf_name in ('mirror_ports', 'ignore_vlans', 'ignore_ports', 'trunk_ports'):
            json_conf = getattr(self, json_conf_name)
            if isinstance(json_conf, str):
                setattr(self, json_conf_name, json.loads(json_conf))

        super(FaucetProxy, self).__init__(
            self.mirror_ports,
            self.reinvestigation_frequency,
            self.max_concurrent_reinvestigations,
            self.ignore_vlans,
            self.ignore_ports,
            self.tunnel_vlan,
            self.tunnel_name,
            *args, **kwargs)

        # parse volos config
        self.volos = Volos(controller)
        self.coprocessor = Coprocessor(controller)
        self.logger = logging.getLogger('faucet')
        self.mac_table = {}

    @staticmethod
    def format_endpoints(data):
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
            md['controller'] = ''
            md['name'] = None
            ret_list.append(md)
        return ret_list

    def get_endpoints(self, messages=None):
        retval = []

        if messages:
            self.logger.debug('faucet messages: {0}'.format(messages))
            for message in messages:
                if not self.ignore_event(message):
                    self.event(message)
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
        self.config(self.config_file, 'shutdown', int(port), switch)
        # TODO check if config was successfully updated
        return shutdowns

    def shutdown_endpoint(self):
        port = 0
        switch = None
        self.config(self.config_file, 'shutdown', int(port), switch)
        # TODO check if config was successfully updated

    def mirror_mac(self, my_mac, my_switch, my_port):
        self.logger.debug('mirroring mac %s', my_mac)
        port = None
        switch = None
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']
        if port and switch:
            self.config(self.config_file, 'mirror', int(port), switch)
        return True

    def unmirror_mac(self, my_mac, my_switch, my_port):
        self.logger.debug('unmirroring mac %s', my_mac)
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
        self.config(self.config_file, 'coprocess', int(port), switch)
        return True

    def uncoprocess_mac(self, my_mac):
        self.logger.debug('uncoprocess mac: {0}'.format(my_mac))
        port = 0
        for mac in self.mac_table:
            if my_mac == mac:
                port = self.mac_table[mac][0]['port']
                switch = self.mac_table[mac][0]['segment']

                self.config(self.config_file, 'uncoprocess',
                            int(port), switch)
        return True
