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
"""
Created on 19 November 2017
@author: cglewis
"""
import yaml

from poseidon.baseClasses.Logger_Base import Logger


def represent_none(dumper, _):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')


class Parser:

    def __init__(self, mirror_ports=None):
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.mirror_ports = mirror_ports

    def config(self, config_file, action, port, switch):
        switch_found = None
        # TODO check for other files
        if not config_file:
            # default to FAUCET default
            config_file = '/etc/faucet/faucet.yaml'
        try:
            stream = open(config_file, 'r')
            obj_doc = yaml.safe_load(stream)
            stream.close()
        except Exception as e:
            self.logger.error(
                'Failed to load config because: {0}'.format(str(e)))
            return False

        if action == 'mirror' or action == 'unmirror':
            ok = True
            if not self.mirror_ports:
                self.logger.error('Unable to mirror, no mirror ports defined')
                return False
            if not 'dps' in obj_doc:
                self.logger.warning(
                    'Unable to find switch configs in {0}'.format(config_file))
                ok = False
            else:
                for s in obj_doc['dps']:
                    if switch == s:
                        switch_found = s
            if not switch_found:
                self.logger.warning('No switch match found to mirror '
                                    'from in the configs. switch: {0} {1}'.format(switch, str(obj_doc)))
                ok = False
            else:
                if not switch_found in self.mirror_ports:
                    self.logger.warning('Unable to mirror {0} on {1}, mirror port not defined on that switch'.format(
                        str(port), str(switch_found)))
                    ok = False
                else:
                    if not port in obj_doc['dps'][switch_found]['interfaces']:
                        self.logger.warning('No port match found for port {0} '
                                            ' to mirror from the switch {1} in '
                                            ' the configs'.format(str(port), obj_doc['dps'][switch_found]['interfaces']))
                        ok = False
                    if not self.mirror_ports[switch_found] in obj_doc['dps'][switch_found]['interfaces']:
                        self.logger.warning('No port match found for port {0} '
                                            'to mirror from the switch {1} in '
                                            'the configs'.format(str(self.mirror_ports[switch_found]), obj_doc['dps'][switch_found]['interfaces']))
                        ok = False
                    else:
                        if 'mirror' in obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]:
                            if not isinstance(obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'], list):
                                obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'] = [
                                    obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror']]
                        else:
                            obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'] = [
                            ]
            if ok:
                if action == 'mirror':
                    if not port in obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'] and port is not None:
                        obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'].append(
                            port)
                elif action == 'unmirror':
                    try:
                        # TODO check for still running captures on this port
                        obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'].remove(
                            port)
                    except ValueError:
                        self.logger.warning('This port: {0} was not already '
                                            'mirroring on this switch: {1}'.format(str(port), str(switch_found)))
            else:
                self.logger.error('Unable to mirror due to warnings')
                return False
        elif action == 'shutdown':
            # TODO
            pass
        else:
            self.logger.warning('Unknown action: {0}'.format(action))
        try:
            if len(obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror']) == 0:
                obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]].remove(
                    'mirror')
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

        stream = open(config_file, 'w')
        yaml.add_representer(type(None), represent_none)
        yaml.dump(obj_doc, stream, default_flow_style=False)

        return True

    def event(self, message):
        data = {}
        if 'L2_LEARN' in message:
            self.poseidon_logger.debug(
                'got faucet message for l2_learn: {0}'.format(message))
            data['ip-address'] = message['L2_LEARN']['l3_src_ip']
            data['ip-state'] = 'L2 learned'
            data['mac'] = message['L2_LEARN']['eth_src']
            data['segment'] = str(message['dp_name'])
            data['port'] = str(message['L2_LEARN']['port_no'])
            data['tenant'] = 'VLAN'+str(message['L2_LEARN']['vid'])
            data['active'] = 1
            if message['L2_LEARN']['eth_src'] in self.mac_table:
                dup = False
                for d in self.mac_table[message['L2_LEARN']['eth_src']]:
                    if data == d:
                        dup = True
                if dup:
                    self.mac_table[message['L2_LEARN']['eth_src']].remove(data)
                self.mac_table[message['L2_LEARN']['eth_src']].insert(0, data)
            else:
                self.mac_table[message['L2_LEARN']['eth_src']] = [data]
        elif 'L2_EXPIRE' in message:
            self.poseidon_logger.debug(
                'got faucet message for l2_expire: {0}'.format(message))
            if message['L2_EXPIRE']['eth_src'] in self.mac_table:
                self.mac_table[message['L2_EXPIRE']
                               ['eth_src']][0]['active'] = 0
        elif 'PORT_CHANGE' in message:
            self.poseidon_logger.debug(
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
        self.poseidon_logger.debug('parsing log file')
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
