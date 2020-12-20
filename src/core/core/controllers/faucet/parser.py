# -*- coding: utf-8 -*-
"""
Created on 19 November 2017
@author: Charlie Lewis
"""
import logging
from collections import defaultdict

from poseidon_core.controllers.faucet.acls import ACLs
from poseidon_core.controllers.faucet.config import FaucetLocalConfGetSetter
from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.controllers.faucet.helpers import parse_rules
from poseidon_core.volos.acls import Acl


class Parser:

    def __init__(self,
                 mirror_ports=None,
                 proxy_mirror_ports=None,
                 reinvestigation_frequency=None,
                 max_concurrent_reinvestigations=None,
                 ignore_vlans=None,
                 ignore_ports=None,
                 tunnel_vlan=None,
                 tunnel_name=None,
                 faucetconfrpc_address=None,
                 faucetconfrpc_client=None,
                 copro_port=None,
                 copro_vlan=None,
                 faucetconfgetsetter_cl=FaucetRemoteConfGetSetter):
        self.logger = logging.getLogger('parser')
        self.mirror_ports = mirror_ports
        self.proxy_mirror_ports = proxy_mirror_ports
        self.reinvestigation_frequency = reinvestigation_frequency
        self.max_concurrent_reinvestigations = max_concurrent_reinvestigations
        self.ignore_vlans = ignore_vlans
        self.ignore_ports = ignore_ports
        self.copro_port = copro_port
        self.copro_vlan = copro_vlan
        self.tunnel_vlan = tunnel_vlan
        self.tunnel_name = tunnel_name
        if faucetconfrpc_address is None:
            faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        if faucetconfrpc_address:
            server = faucetconfrpc_address.split(':')[0]
        else:
            server = ''
        self.faucetconfgetsetter = faucetconfgetsetter_cl(
            client_key='/certs/%s.key' % faucetconfrpc_client,
            client_cert='/certs/%s.crt' % faucetconfrpc_client,
            ca_cert='/certs/%s-ca.crt' % server,
            server_addr=faucetconfrpc_address)
        self.mac_table = {}
        self.mirror_counts = defaultdict(int)
        self._set_default_switch_conf()

    def _read_faucet_conf(self):
        return self.faucetconfgetsetter.read_faucet_conf(config_file=None)

    def _write_faucet_conf(self, faucet_conf=None):
        return self.faucetconfgetsetter.write_faucet_conf(config_file=None, faucet_conf=faucet_conf)

    def _get_dps(self):
        return self.faucetconfgetsetter.get_dps()

    def _get_switch_conf(self, dp):
        return self.faucetconfgetsetter.get_switch_conf(dp)

    def _get_port_conf(self, dp, port):
        return self.faucetconfgetsetter.get_port_conf(dp, port)

    def _get_stack_root_switch(self):
        return self.faucetconfgetsetter.get_stack_root_switch()

    def _get_acls(self):
        faucet_conf = self._read_faucet_conf()
        acls = Acl(faucetconfgetsetter=self.faucetconfgetsetter)
        acls.read(config_yaml=faucet_conf)
        return acls

    def _set_acls(self, acls):
        self.faucetconfgetsetter.set_acls(acls)

    def _update_switch_conf(self, dp, switch_conf):
        self.faucetconfgetsetter.update_switch_conf(dp, switch_conf)

    def _set_port_conf(self, dp, port, port_conf):
        self.faucetconfgetsetter.set_port_conf(dp, port, port_conf)

    def _clear_mirror_port(self, switch, port):
        self.faucetconfgetsetter.clear_mirror_port(switch, port)

    def _mirror_port(self, switch, mirror_port, port):
        self.faucetconfgetsetter.mirror_port(switch, mirror_port, port)

    def _unmirror_port(self, switch, mirror_port, port):
        self.faucetconfgetsetter.unmirror_port(switch, mirror_port, port)

    def _set_default_switch_conf(self):
        # TODO: make smarter with more complex configs (backup original values, etc)
        if self.mirror_ports:
            root_stack_switch = self._get_stack_root_switch()
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
                self._set_acls(acls.acls)

            for switch, mirror_port in self.mirror_ports.items():
                if not self._get_switch_conf(switch):
                    continue
                if self.reinvestigation_frequency:
                    switch_conf = {
                        'timeout': (self.reinvestigation_frequency * 2) + 1,
                        'arp_neighbor_timeout': self.reinvestigation_frequency}
                    self._update_switch_conf(switch, switch_conf)
                # If stacking was detected, provision tunnel config on non root switches.
                # Poseidon's mirror NIC must be connected to the root switch's mirror port.
                # Non mirror switches must have a loopback plug installed in their mirror port.
                if root_stack_switch and root_mirror_port:
                    mirror_port_conf = self._get_port_conf(switch, mirror_port)
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
                    self._set_port_conf(switch, mirror_port, mirror_port_conf)

    def proxy_mirror_port(self, switch, port):
        self.logger.debug('checking for proxy ports')
        if self.proxy_mirror_ports and self._get_switch_conf(switch):
            proxy_ports = self.proxy_mirror_ports.get(switch, None)
            if proxy_ports:
                self.logger.debug(f'found proxy port: {switch} port {port}')
                switch, port = proxy_ports
        return switch, port

    def mirror_switch_port(self, switch):
        if self.mirror_ports:
            switch_mirror_port = self.mirror_ports.get(switch, None)
            if switch_mirror_port:
                if self._get_port_conf(switch, switch_mirror_port):
                    return switch_mirror_port
        self.logger.warning('no mirror port for switch %s' % switch)
        return None

    def clear_mirrors(self):
        dps = self._get_dps()
        if dps:
            for switch in dps:
                mirror_port = self.mirror_switch_port(switch)
                if mirror_port:
                    self._clear_mirror_port(switch, mirror_port)

    def config_mirror(self, action, switch, port):
        switch, port = self.proxy_mirror_port(switch, port)
        mirror_port = self.mirror_switch_port(switch)
        if mirror_port:
            mirror_key = (switch, port)
            if action in ('mirror', 'unmirror'):
                self.logger.info(f'request {action} of {mirror_key}')
                if action == 'mirror':
                    self._mirror_port(switch, mirror_port, port)
                    self.mirror_counts[mirror_key] += 1
                elif action == 'unmirror':
                    if self.mirror_counts[mirror_key]:
                        self.mirror_counts[mirror_key] -= 1
                        if not self.mirror_counts[mirror_key]:
                            self.logger.info(
                                f'removing last remaining mirror on {mirror_key}')
                            self._unmirror_port(switch, mirror_port, port)
                count = self.mirror_counts[mirror_key]
                self.logger.info(f'mirroring {count} MACs on {mirror_key}')
            else:
                self.logger.error(f'Unknown mirror action {action} for {mirror_key}')
        else:
            self.logger.error(
                f'Unable to configure mirror/unmirror {switch}:{port} due to warnings')

    def config_acls(self, rules_file, endpoints, force_apply_rules, force_remove_rules, coprocess_rules_files):
        rules_doc = parse_rules(rules_file)
        self._read_faucet_conf()
        self.faucetconfgetsetter.faucet_conf = ACLs().apply_acls(
            rules_file, endpoints,
            force_apply_rules, force_remove_rules,
            coprocess_rules_files, self.faucetconfgetsetter.faucet_conf, rules_doc)
        self._write_faucet_conf()

    def config(self, action, port, switch, rules_file=None,
               endpoints=None, force_apply_rules=None, force_remove_rules=None,
               coprocess_rules_files=None):
        if action in ('shutdown', 'apply_routes'):
            # TODO: not implemented.
            pass
        elif action in ('mirror', 'unmirror'):
            self.config_mirror(action, switch, port)
        elif action == 'apply_acls':
            self.config_acls(
                rules_file, endpoints, force_apply_rules, force_remove_rules, coprocess_rules_files)
        else:
            self.logger.warning('Unknown action: {0}'.format(action))

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
                        'ignoring event because learning from a stack port')
                    return True
                if self.ignore_vlans:
                    if vlan in self.ignore_vlans:
                        self.logger.debug(
                            'ignoring event because VLAN %s ignored' % vlan)
                        return True
                if self.ignore_ports:
                    for ignore_switch, ignore_port_no in self.ignore_ports.items():
                        if ignore_switch == switch and ignore_port_no == port_no:
                            self.logger.debug(
                                'ignoring event because switch %s port %s is ignored' % (
                                    switch, port_no))
                            return True
                if self.proxy_mirror_ports:
                    for s in self.proxy_mirror_ports:
                        if (switch == self.proxy_mirror_ports[s][0] and
                            port_no == self.proxy_mirror_ports[s][1]):
                            self.logger.debug(
                                'ignoring event because switch %s port %s is being a proxy' % (
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
                'got faucet message for l2_learn: {0}'.format(message))
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
