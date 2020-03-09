# -*- coding: utf-8 -*-
"""
Created on 19 November 2017
@author: Charlie Lewis
"""
import logging
from copy import deepcopy

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
                 copro_port=None,
                 copro_vlan=None):
        self.logger = logging.getLogger('parser')
        self.mirror_ports = mirror_ports
        self.reinvestigation_frequency = reinvestigation_frequency
        self.max_concurrent_reinvestigations = max_concurrent_reinvestigations
        self.ignore_vlans = ignore_vlans
        self.copro_port = copro_port
        self.copro_vlan = copro_vlan

    @staticmethod
    def clear_mirrors(config_file):
        config_file = get_config_file(config_file)
        obj_doc = yaml_in(config_file)
        if obj_doc:
            # TODO make this smarter about more complex configurations (backup original values, etc)
            obj_copy = deepcopy(obj_doc)
            if 'dps' in obj_copy:
                for switch in obj_copy['dps']:
                    if 'interfaces' in obj_copy['dps'][switch]:
                        for port in obj_copy['dps'][switch]['interfaces']:
                            if 'mirror' in obj_copy['dps'][switch]['interfaces'][port]:
                                del obj_doc['dps'][switch]['interfaces'][port]['mirror']
                    if 'timeout' in obj_copy['dps'][switch]:
                        del obj_doc['dps'][switch]['timeout']
                    if 'arp_neighbor_timeout' in obj_copy['dps'][switch]:
                        del obj_doc['dps'][switch]['arp_neighbor_timeout']
                return yaml_out(config_file, obj_doc)
        return False

    def check_mirror(self, config_file, switch, port, obj_doc):
        if not obj_doc:
            self.logger.error('No config found')
            return False
        if not self.mirror_ports:
            self.logger.error('Unable to mirror, no mirror ports defined')
            return False
        if 'dps' not in obj_doc:
            self.logger.error(f'Unable to find switches in {config_file}')
            return False

        for s in obj_doc['dps']:
            if (switch == s and s in self.mirror_ports and
                'interfaces' in obj_doc['dps'][s] and
                port in obj_doc['dps'][s]['interfaces'] and
                    self.mirror_ports[s] in obj_doc['dps'][s]['interfaces']):
                return s

        self.logger.error(f'No switch/port match found to mirror from in '
                          'the configs or mirror port not defined on that '
                          'switch: {switch} {obj_doc}')
        return False

    def config(self, config_file, action, port, switch, rules_file=None,
               endpoints=None, force_apply_rules=None, force_remove_rules=None,
               coprocess_rules_files=None):
        switch_found = None
        config_file = get_config_file(config_file)
        obj_doc = yaml_in(config_file)

        switch_found = self.check_mirror(config_file, switch, port, obj_doc)

        if action == 'mirror' or action == 'unmirror':
            if switch_found:
                interfaces = obj_doc['dps'][switch_found]['interfaces']
                if 'mirror' in interfaces[self.mirror_ports[switch_found]]:
                    if not isinstance(interfaces[self.mirror_ports[switch_found]]['mirror'], list):
                        interfaces[self.mirror_ports[switch_found]]['mirror'] = [
                            interfaces[self.mirror_ports[switch_found]]['mirror']]
                else:
                    interfaces[self.mirror_ports[switch_found]]['mirror'] = [
                    ]
                if action == 'mirror':
                    # TODO make this smarter about more complex configurations (backup original values, etc)
                    if self.reinvestigation_frequency:
                        obj_doc['dps'][switch_found]['timeout'] = (
                            self.reinvestigation_frequency * 2) + 1
                    else:
                        obj_doc['dps'][switch_found]['timeout'] = self.reinvestigation_frequency
                    obj_doc['dps'][switch_found]['arp_neighbor_timeout'] = self.reinvestigation_frequency
                    if port not in interfaces[self.mirror_ports[switch_found]]['mirror'] and port is not None:
                        interfaces[self.mirror_ports[switch_found]]['mirror'].append(
                            port)
                elif action == 'unmirror':
                    try:
                        # TODO check for still running captures on this port
                        interfaces[self.mirror_ports[switch_found]]['mirror'].remove(
                            port)
                    except ValueError:
                        self.logger.warning('Port: {0} was not already '
                                            'mirroring on this switch: {1}'.format(str(port), str(switch_found)))
            else:
                self.logger.error('Unable to mirror due to warnings')
                return switch_found
        elif action == 'shutdown':
            # TODO
            pass
        elif action == 'apply_acls':
            rules_doc = parse_rules(rules_file)
            obj_doc = ACLs().apply_acls(config_file, rules_file, endpoints,
                                        force_apply_rules, force_remove_rules,
                                        coprocess_rules_files, obj_doc,
                                        rules_doc)
        elif action == 'apply_routes':
            # TODO
            pass
        else:
            self.logger.warning('Unknown action: {0}'.format(action))

        if switch_found:
            try:
                if len(obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror']) == 0:
                    del obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror']
                    # TODO make this smarter about more complex configurations (backup original values, etc)
                    if 'timeout' in obj_doc['dps'][switch_found]:
                        del obj_doc['dps'][switch_found]['timeout']
                    if 'arp_neighbor_timeout' in obj_doc['dps'][switch_found]:
                        del obj_doc['dps'][switch_found]['arp_neighbor_timeout']
                else:
                    ports = []
                    for p in obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror']:
                        if p:
                            ports.append(p)
                    obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]
                                                               ]['mirror'] = ports
            except Exception as e:
                self.logger.warning(
                    'Unable to remove empty mirror list because: {0}'.format(str(e)))

        yaml_out(config_file, obj_doc)
        return

    def event(self, message):
        data = {}
        if 'L2_LEARN' in message:
            ignore = False
            if self.ignore_vlans:
                for vlan in self.ignore_vlans:
                    if vlan == message['L2_LEARN']['vid']:
                        ignore = True
            if self.ignore_ports:
                for switch in self.ignore_ports:
                    if self.ignore_ports[switch] == message['L2_LEARN']['port_no'] and switch == str(message['dp_name']):
                        ignore = True
            self.logger.debug(
                'got faucet message for l2_learn: {0}'.format(message))
            if not ignore:
                data['ip-address'] = message['L2_LEARN']['l3_src_ip']
                data['ip-state'] = 'L2 learned'
                data['mac'] = message['L2_LEARN']['eth_src']
                data['segment'] = str(message['dp_name'])
                data['port'] = str(message['L2_LEARN']['port_no'])
                data['vlan'] = 'VLAN'+str(message['L2_LEARN']['vid'])
                data['tenant'] = 'VLAN'+str(message['L2_LEARN']['vid'])
                data['active'] = 1
                if message['L2_LEARN']['eth_src'] in self.mac_table:
                    dup = False
                    for d in self.mac_table[message['L2_LEARN']['eth_src']]:
                        if data == d:
                            dup = True
                    if dup:
                        self.mac_table[message['L2_LEARN']
                                       ['eth_src']].remove(data)
                    self.mac_table[message['L2_LEARN']
                                   ['eth_src']].insert(0, data)
                else:
                    self.mac_table[message['L2_LEARN']['eth_src']] = [data]
            else:
                self.logger.debug(
                    'ignoring endpoint because it belongs to the ignore_vlans or ignore_ports list')
        elif 'L2_EXPIRE' in message:
            self.logger.debug(
                'got faucet message for l2_expire: {0}'.format(message))
            if message['L2_EXPIRE']['eth_src'] in self.mac_table:
                self.mac_table[message['L2_EXPIRE']
                               ['eth_src']][0]['active'] = 0
        elif 'PORT_CHANGE' in message:
            self.logger.debug(
                'got faucet message for port_change: {0}'.format(message))
            if not message['PORT_CHANGE']['status']:
                m_table = self.mac_table.copy()
                for mac in m_table:
                    for data in m_table[mac]:
                        if (str(message['PORT_CHANGE']['port_no']) == data['port'] and
                                str(message['dp_name']) == data['segment']):
                            if mac in self.mac_table:
                                self.mac_table[mac][0]['active'] = 0
        return

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
        return
