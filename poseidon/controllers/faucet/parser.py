# -*- coding: utf-8 -*-
"""
Created on 19 November 2017
@author: Charlie Lewis
"""
import logging

from poseidon.controllers.faucet.acls import ACLs
from poseidon.controllers.faucet.helpers import get_config_file
from poseidon.controllers.faucet.helpers import parse_rules
from poseidon.controllers.faucet.helpers import yaml_in
from poseidon.controllers.faucet.helpers import yaml_out


class Parser:

    def __init__(self,
                 mirror_ports=None,
                 reinvestigation_frequency=None,
                 max_concurrent_reinvestigations=None,
                 ignore_vlans=None,
                 ignore_ports=None,
                 copro_port=None,
                 copro_vlan=None):
        self.logger = logging.getLogger('parser')
        self.mirror_ports = mirror_ports
        self.reinvestigation_frequency = reinvestigation_frequency
        self.max_concurrent_reinvestigations = max_concurrent_reinvestigations
        self.ignore_vlans = ignore_vlans
        self.ignore_ports = ignore_ports
        self.copro_port = copro_port
        self.copro_vlan = copro_vlan
        self.mac_table = {}

    @staticmethod
    def _write_faucet_conf(config_file, faucet_conf):
        config_file = get_config_file(config_file)
        return yaml_out(config_file, faucet_conf)

    @staticmethod
    def _read_faucet_conf(config_file):
        config_file = get_config_file(config_file)
        faucet_conf = yaml_in(config_file)
        return faucet_conf

    def set_mirror_config(self, switch_conf, mirror_interface_conf, ports):
        # TODO: make smarter with more complex configs (backup original values, etc)
        if self.reinvestigation_frequency:
            switch_conf['timeout'] = (self.reinvestigation_frequency * 2) + 1
        else:
            switch_conf['timeout'] = self.reinvestigation_frequency
        switch_conf['arp_neighbor_timeout'] = self.reinvestigation_frequency
        if ports:
            if not isinstance(ports, list):
                ports = list(ports)
            mirror_interface_conf['mirror'] = ports
        # Don't delete timeout/arp_neighbor_timeout when setting mirror list to empty,
        # as that could cause an unnecessary cold start.
        elif 'mirror' in mirror_interface_conf:
            del mirror_interface_conf['mirror']

    def check_mirror(self, switch, faucet_conf):
        switch_conf = None
        mirror_interface_conf = None
        existing_mirror_ports = []

        if not faucet_conf:
            self.logger.error('No config found')
        elif not self.mirror_ports:
            self.logger.error('Unable to mirror, no mirror ports defined')
        else:
            dps = faucet_conf.get('dps', None)
            if dps is not None:
                switch_conf = dps.get(switch, None)
                switch_mirror_port = self.mirror_ports.get(switch, None)
                if switch_conf is not None and switch_mirror_port is not None:
                    interfaces_conf = switch_conf.get('interfaces', None)
                    if interfaces_conf:
                        mirror_interface_conf = interfaces_conf.get(switch_mirror_port, None)
                        if mirror_interface_conf:
                            existing_mirror_ports = mirror_interface_conf.get('mirror', [])
                            if not isinstance(existing_mirror_ports, list):
                                existing_mirror_ports = list(existing_mirror_ports)
                            existing_mirror_ports = set(existing_mirror_ports)

        return (switch_conf, mirror_interface_conf, existing_mirror_ports)

    def clear_mirrors(self, config_file):
        faucet_conf = self._read_faucet_conf(config_file)
        if faucet_conf:
            dps = faucet_conf.get('dps', None)
            if dps:
                for switch in dps:
                    switch_conf, mirror_interface_conf, _ = self.check_mirror(switch, faucet_conf)
                    if switch_conf and mirror_interface_conf:
                        self.set_mirror_config(switch_conf, mirror_interface_conf, None)
                return self._write_faucet_conf(config_file, faucet_conf)
        return False

    def config(self, config_file, action, port, switch, rules_file=None,
               endpoints=None, force_apply_rules=None, force_remove_rules=None,
               coprocess_rules_files=None):
        faucet_conf = self._read_faucet_conf(config_file)
        switch_conf, mirror_interface_conf, mirror_ports = self.check_mirror(switch, faucet_conf)

        if action in ('shutdown', 'apply_routes'):
            # TODO: not implemented.
            pass
        elif action in ('mirror', 'unmirror'):
            if switch_conf and mirror_interface_conf:
                if action == 'mirror':
                    mirror_ports.add(port)
                elif action == 'unmirror':
                    try:
                        # TODO check for still running captures on this port
                        mirror_ports.remove(port)
                    except ValueError:
                        self.logger.warning(
                            'Port: {0} was not already mirroring on this switch: {1}'.format(
                                str(port), str(switch)))
            else:
                self.logger.error('Unable to mirror due to warnings')
        elif action == 'apply_acls':
            rules_doc = parse_rules(rules_file)
            faucet_conf = ACLs().apply_acls(
                config_file, rules_file, endpoints,
                force_apply_rules, force_remove_rules,
                coprocess_rules_files, faucet_conf, rules_doc)
        else:
            self.logger.warning('Unknown action: {0}'.format(action))

        if switch_conf and mirror_interface_conf:
            self.set_mirror_config(switch_conf, mirror_interface_conf, mirror_ports)

        self._write_faucet_conf(config_file, faucet_conf)

    def ignore_event(self, message):
        for message_type in ('L2_LEARN', 'L2_EXPIRE', 'PORT_CHANGE'):
            message_body = message.get(message_type, None)
            if message_body:
                # When stacking is in use, we only want to learn on switch, that a host is local to.
                if 'stack_descr' in message_body:
                    self.logger.debug('ignoring event because learning from a stack port')
                    return True
                if self.ignore_vlans:
                    vlan = message_body.get('vid', None)
                    if vlan in self.ignore_vlans:
                        self.logger.debug('ignoring event because VLAN %s ignored' % vlan)
                        return True
                if self.ignore_ports:
                    switch = str(message['dp_name'])
                    port_no = message_body.get('port_no', None)
                    for ignore_switch, ignore_port_no in self.ignore_ports.items():
                        if ignore_switch == switch and ignore_port_no == port_no:
                            self.logger.debug(
                                'ignoring event because switch %s port %s is ignored' % (
                                    switch, port_no))
                            return True
                # Not on any ignore list, don't ignore.
                return False
        # Not a message we are interested in, ignore it.
        return True

    def event(self, message):
        dp_name = str(message['dp_name'])
        def make_mac_inactive(mac):
            if mac in self.mac_table:
                self.mac_table[mac][0]['active'] = 0

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
        elif 'L2_EXPIRE' in message:
            self.logger.debug(
                'got faucet message for l2_expire: {0}'.format(message))
            message = message['L2_EXPIRE']
            make_mac_inactive(message['eth_src'])
        elif 'PORT_CHANGE' in message:
            self.logger.debug(
                'got faucet message for port_change: {0}'.format(message))
            message = message['PORT_CHANGE']
            port_no_str = str(message['port_no'])
            if not message['status']:
                m_table = self.mac_table.copy()
                for mac in m_table:
                    for data in m_table[mac]:
                        if port_no_str == data['port'] and dp_name == data['segment']:
                            make_mac_inactive(mac)

    def log(self, log_file):
        self.logger.debug('parsing log file')
        if not log_file:
            # default to FAUCET default
            log_file = '/var/log/faucet/faucet.log'
        # NOTE very fragile, prone to errors
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if 'L2 learned' in line:
                        learned_mac = line.split()
                        data = {'ip-address': learned_mac[16][0:-1],
                                'ip-state': 'L2 learned',
                                'mac': learned_mac[10],
                                'segment': learned_mac[7][1:-1],
                                'port': learned_mac[22],
                                'tenant': learned_mac[24] + learned_mac[25],
                                'active': 1}
                        if learned_mac[10] in self.mac_table:
                            dup = False
                            for d in self.mac_table[learned_mac[10]]:
                                if data == d:
                                    dup = True
                            if dup:
                                self.mac_table[learned_mac[10]].remove(data)
                            self.mac_table[learned_mac[10]].insert(0, data)
                        else:
                            self.mac_table[learned_mac[10]] = [data]
                    elif ', expired [' in line:
                        expired_mac = line.split(', expired [')
                        expired_mac = expired_mac[1].split()[0]
                        if expired_mac in self.mac_table:
                            self.mac_table[expired_mac][0]['active'] = 0
                    elif ' Port ' in line:
                        # try and see if it was a port down event
                        # this will break if more than one port expires at the same time TODO
                        port_change = line.split(' Port ')
                        dpid = port_change[0].split()[-2]
                        port_change = port_change[1].split()
                        if port_change[1] == 'down':
                            m_table = self.mac_table.copy()
                            for mac in m_table:
                                for data in m_table[mac]:
                                    if (port_change[0] == data['port'] and
                                            dpid == data['segment']):
                                        self.mac_table[mac][0]['active'] = 0
        except Exception as e:
            self.logger.error(
                'Error parsing Faucet log file {0}'.format(str(e)))
