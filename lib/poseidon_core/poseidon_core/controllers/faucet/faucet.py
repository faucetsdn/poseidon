# -*- coding: utf-8 -*-
'''
Created on 17 November 2017
@author: Charlie Lewis
'''
import ipaddress
import logging
from collections import defaultdict

from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.helpers.config import parse_rules
from poseidon_core.operations.primitives.acl import ACL
from poseidon_core.operations.primitives.coprocess import Coprocess
from poseidon_core.operations.volos.acls import Acl
from poseidon_core.operations.volos.volos import Volos


class FaucetProxy:

    def __init__(self,
                 config,
                 *args,
                 **kwargs):
        '''Initializes Faucet object.'''
        self.mirror_ports = kwargs.get('mirror_ports', config['MIRROR_PORTS'])
        self.proxy_mirror_ports = kwargs.get(
            'proxy_mirror_ports', config['controller_proxy_mirror_ports'])
        self.tunnel_vlan = kwargs.get('tunnel_vlan', config['tunnel_vlan'])
        self.tunnel_name = kwargs.get('tunnel_name', config['tunnel_name'])
        self.learn_pub_adds = kwargs.get(
            'learn_pub_adds', config['LEARN_PUBLIC_ADDRESSES'])
        self.reinvestigation_frequency = kwargs.get(
            'reinvestigation_frequency', config['reinvestigation_frequency'])
        self.max_concurrent_reinvestigations = kwargs.get(
            'max_concurrent_reinvestigations', config['max_concurrent_reinvestigations'])
        self.trunk_ports = kwargs.get('trunk_ports', config['trunk_ports'])
        self.ignore_vlans = kwargs.get('ignore_vlans', config['ignore_vlans'])
        self.ignore_ports = kwargs.get('ignore_ports', config['ignore_ports'])
        self.mirror_counts = kwargs.get('mirror_counts', defaultdict(int))
        self.frpc = None
        faucetconfgetsetter_cl = kwargs.get(
            'faucetconfgetsetter_cl', FaucetRemoteConfGetSetter)
        self._get_frpc(config, faucetconfgetsetter_cl=faucetconfgetsetter_cl)
        self._set_default_switch_conf()
        self.logger = logging.getLogger('faucet')
        self.mac_table = {}

        # parse volos config
        self.volos = Volos(config)
        self.coprocessor = Coprocess(config)

    def _get_acls(self):
        faucet_conf = self.frpc.read_faucet_conf(config_file=None)
        acls = Acl(faucetconfgetsetter=self.frpc)
        acls.read(config_yaml=faucet_conf)
        return acls

    def _set_default_switch_conf(self):
        # TODO: make smarter with more complex configs (backup original values, etc)
        if self.mirror_ports:
            root_stack_switch = self.frpc.get_stack_root_switch()
            root_mirror_port = None
            if root_stack_switch:
                acls = self._get_acls()
                root_mirror_port = self.mirror_ports.get(
                    root_stack_switch, None)
                if self.tunnel_name in acls.acls:
                    del acls.acls[self.tunnel_name]
                # Safety rule to prevent looped packets being output to the loop.
                acls.add_rule(
                    self.tunnel_name,
                    {'rule': {'vlan_vid': self.tunnel_vlan, 'actions': {'allow': 0}}})
                # Tunnel back to root.
                acls.add_rule(
                    self.tunnel_name,
                    {'rule': {'actions': {'allow': 0, 'output': {'tunnel': {
                        'type': 'vlan', 'tunnel_id': self.tunnel_vlan,
                        'dp': root_stack_switch, 'port': root_mirror_port}}}}})
                # Merge ACL updates, if any back in
                self.frpc.set_acls(acls.acls)

            for switch, mirror_port in self.mirror_ports.items():
                if not self.frpc.get_switch_conf(switch):
                    continue
                if self.reinvestigation_frequency:
                    switch_conf = {
                        'timeout': (self.reinvestigation_frequency * 2) + 1,
                        'arp_neighbor_timeout': self.reinvestigation_frequency}
                    self.frpc.update_switch_conf(switch, switch_conf)
                # If stacking was detected, provision tunnel config on non root switches.
                # Poseidon's mirror NIC must be connected to the root switch's mirror port.
                # Non mirror switches must have a loopback plug installed in their mirror port.
                if root_stack_switch and root_mirror_port:
                    mirror_port_conf = self.frpc.get_port_conf(
                        switch, mirror_port)
                    if not mirror_port_conf:
                        continue
                    for existing_key in set(mirror_port_conf.keys()):
                        if existing_key not in ('mirror',):
                            del mirror_port_conf[existing_key]
                    if root_stack_switch == switch:
                        mirror_port_conf.update({
                            'description': 'Poseidon local mirror',
                            'output_only': True,
                        })
                    else:
                        mirror_port_conf.update({
                            'description': 'Poseidon remote mirror (loopback plug)',
                            'acls_in': [self.tunnel_name],
                            'coprocessor': {'strategy': 'vlan_vid'},
                        })
                    self.frpc.set_port_conf(
                        switch, mirror_port, mirror_port_conf)

    def _get_frpc(self, config, faucetconfgetsetter_cl=FaucetRemoteConfGetSetter):
        faucetconfrpc_address = config['faucetconfrpc_address']
        faucetconfrpc_client = config['faucetconfrpc_client']
        if faucetconfrpc_address:
            server = faucetconfrpc_address.split(':')[0]
        else:
            server = ''
        self.frpc = faucetconfgetsetter_cl(
            client_key='/certs/%s.key' % faucetconfrpc_client,
            client_cert='/certs/%s.crt' % faucetconfrpc_client,
            ca_cert='/certs/%s-ca.crt' % server,
            server_addr=faucetconfrpc_address)

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

            md.update({
                'controller_type': 'faucet',
                'controller': '',
                'name': None})
            ret_list.append(md)
        return ret_list

    def ignore_event(self, message):
        for message_type in ('L2_LEARN',):
            message_body = message.get(message_type, None)
            if message_body:
                switch = str(message['dp_name'])
                port_no = message_body.get('port_no', None)
                vlan = message_body.get('vid', None)
                # When stacking is in use, we only want to learn on switch, that a host is local to.
                if 'stack_descr' in message_body:
                    self.logger.debug(
                        'Ignoring event because learning from a stack port')
                    return True
                if self.ignore_vlans:
                    if vlan in self.ignore_vlans:
                        self.logger.debug(
                            'Ignoring event because VLAN %s ignored' % vlan)
                        return True
                if self.ignore_ports:
                    for ignore_switch, ignore_port_no in self.ignore_ports.items():
                        if ignore_switch == switch and ignore_port_no == port_no:
                            self.logger.debug(
                                'Ignoring event because switch %s port %s is ignored' % (
                                    switch, port_no))
                            return True
                if self.proxy_mirror_ports:
                    for s in self.proxy_mirror_ports:
                        if (switch == self.proxy_mirror_ports[s][0] and
                                port_no == self.proxy_mirror_ports[s][1]):
                            self.logger.debug(
                                'Ignoring event because switch %s port %s is being a proxy' % (
                                    switch, port_no))
                            return True
                # Not on any ignore list, don't ignore.
                return False
        # Not a message we are interested in, ignore it.
        return True

    def event(self, message):
        dp_name = str(message['dp_name'])

        if 'L2_LEARN' in message:
            self.logger.debug(
                'Got faucet message for l2_learn: {0}'.format(message))
            message = message['L2_LEARN']
            eth_src = message['eth_src']
            vlan_str = 'VLAN%s' % message['vid']
            data = {
                'ip-address': message['l3_src_ip'],
                'ip-state': 'L2 learned',
                'mac': eth_src,
                'segment': dp_name,
                'port': str(message['port_no']),
                'vlan': vlan_str,
                'tenant': vlan_str,
                'active': 1}

            if eth_src in self.mac_table:
                if data in self.mac_table[eth_src]:
                    self.mac_table[eth_src].remove(data)
                self.mac_table[eth_src].insert(0, data)
            else:
                self.mac_table[eth_src] = [data]

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
                first_entry = self.mac_table[mac][0]
                if 'ip-address' in first_entry and (
                        first_entry['ip-address'] == 'None' or
                        first_entry['ip-address'] is None or
                        not ipaddress.ip_address(first_entry['ip-address']).is_global):
                    retval.append(self.mac_table[mac])
        return retval

    def update_acls(self, rules_file=None, endpoints=None, force_apply_rules=None, force_remove_rules=None):
        self.logger.debug('Updating ACLs')
        rules_doc = parse_rules(rules_file)
        if not rules_doc:
            self.logger.error(
                'Unable to read or parse rules file, not applying ACLs')
            return False
        self.frpc.read_faucet_conf(config_file=None)
        # TODO coprocess_rules_files is set to None, which was previous default but removes functionality
        self.frpc.faucet_conf = ACL(self.frpc).apply_acls(
            rules_file, endpoints,
            force_apply_rules, force_remove_rules,
            None, self.frpc.faucet_conf, rules_doc)
        self.frpc.write_faucet_conf(config_file=None)
        return True

    def _mac_switch_port(self, my_mac):
        try:
            entry = self.mac_table[my_mac][0]
            return (entry['segment'], int(entry['port']))
        except (KeyError, IndexError):
            return (None, None)

    def proxy_mirror_port(self, switch, port):
        self.logger.debug('Checking for proxy ports')
        if self.proxy_mirror_ports and self.frpc.get_switch_conf(switch):
            proxy_ports = self.proxy_mirror_ports.get(switch, None)
            if proxy_ports:
                self.logger.debug(f'Found proxy port: {switch} port {port}')
                switch, port = proxy_ports
        return switch, port

    def mirror_switch_port(self, switch):
        if self.mirror_ports:
            switch_mirror_port = self.mirror_ports.get(switch, None)
            if switch_mirror_port:
                if self.frpc.get_port_conf(switch, switch_mirror_port):
                    return switch_mirror_port
        self.logger.warning('No mirror port for switch %s' % switch)
        return None

    def clear_mirrors(self):
        dps = self.frpc.get_dps()
        if dps:
            for switch in dps:
                mirror_port = self.mirror_switch_port(switch)
                if mirror_port:
                    self.frpc.clear_mirror_port(switch, mirror_port)

    def mirror_mac(self, my_mac, my_switch, my_port):
        self.logger.debug('Mirroring mac %s', my_mac)
        switch, port = self._mac_switch_port(my_mac)
        if switch and port:
            switch, port = self.proxy_mirror_port(switch, port)
            mirror_port = self.mirror_switch_port(switch)
            if mirror_port:
                mirror_key = (switch, port)
                self.logger.info(f'Request mirror of {mirror_key}')
                self.frpc.mirror_port(switch, mirror_port, port)
                self.mirror_counts[mirror_key] += 1
                count = self.mirror_counts[mirror_key]
                self.logger.info(f'Mirroring {count} MACs on {mirror_key}')
            else:
                self.logger.error(
                    f'Unable to configure mirror on {switch}:{port} due to warnings')
                return False
        return True

    def unmirror_mac(self, my_mac, my_switch, my_port):
        self.logger.debug('Unmirroring mac %s', my_mac)
        switch, port = self._mac_switch_port(my_mac)
        if port and switch:
            trunk = False
            for sw in self.trunk_ports:
                if sw == switch and self.trunk_ports[sw].split(',')[1] == str(port):
                    trunk = True
            if not trunk:
                switch, port = self.proxy_mirror_port(switch, port)
                mirror_port = self.mirror_switch_port(switch)
                if mirror_port:
                    mirror_key = (switch, port)
                    self.logger.info(f'Request unmirror of {mirror_key}')
                    if self.mirror_counts[mirror_key]:
                        self.mirror_counts[mirror_key] -= 1
                        if not self.mirror_counts[mirror_key]:
                            self.logger.info(
                                f'Removing last remaining mirror on {mirror_key}')
                            self.frpc.unmirror_port(switch, mirror_port, port)
                        count = self.mirror_counts[mirror_key]
                        self.logger.info(
                            f'Mirroring {count} MACs on {mirror_key}')
                else:
                    self.logger.error(
                        f'Unable to configure unmirror on {switch}:{port} due to warnings')
                    return False
            else:
                self.logger.debug('Not unmirroring a trunk port')
                return False
        return True

    def coprocess_mac(self, my_mac):
        self.logger.debug('coprocess mac: {0}'.format(my_mac))
        switch, port = self._mac_switch_port(my_mac)
        if switch and port:
            # TODO this is an unknown action currently...
            #self.config('coprocess', int(port), switch)
            pass
        return True

    def uncoprocess_mac(self, my_mac):
        self.logger.debug('uncoprocess mac: {0}'.format(my_mac))
        switch, port = self._mac_switch_port(my_mac)
        if switch and port:
            # TODO this is an unknown action currently...
            #self.config('uncoprocess', int(port), switch)
            pass
        return True
