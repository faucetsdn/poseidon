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
from yaml import load, dump
from yaml import CLoader as Loader, CDumper as Dumper

from poseidon.baseClasses.Logger_Base import Logger

module_logger = Logger.logger


class Parser:

    def __init__(self, mirror_ports=None):
        self.logger = module_logger
        self.mirror_ports = mirror_ports

    def config(self, config_file, action, port, switch):
        documents = {}
        stream = open(config_file, 'r')
        obj_doc = load(stream)
        stream.close()
        # TODO check for other files

        if action == 'mirror':
            ok = True
            if not self.mirror_ports:
                self.logger.error("Unable to mirror, no mirror ports defined")
                return None
            if not switch in self.mirror_ports:
                self.logger.warning("Unable to mirror " + str(port) + " on " +
                                    str(switch) +
                                    ", mirror port not defined on that switch")
                ok = False
            else:
                if not 'dps' in obj_doc:
                    self.logger.warning("Unable to find switch configs in "
                                        "'/etc/ryu/faucet/faucet.yaml'")
                    ok = False
                else:
                    switch_found = None
                    for s in obj_doc['dps']:
                        if isinstance(switch, str):
                            if switch == s:
                                switch_found = s
                        elif isinstance(switch, int):
                            if hex(switch) == hex(obj_doc['dps'][s]['dp_id']):
                                switch_found = s
                    if not switch_found:
                        self.logger.warning("No switch match found to mirror "
                                            "from in the configs")
                        ok = False
                    else:
                        if not port in obj_doc['dps'][switch_found]['interfaces']:
                            self.logger.warning("No port match found to "
                                                "mirror from in the configs")
                            ok = False
                        if not self.mirror_ports[switch] in obj_doc['dps'][switch_found]['interfaces']:
                            self.logger.warning("No port match found to "
                                                "mirror to in the configs")
                            ok = False
                        else:
                            if 'mirror' in obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch]]:
                                self.logger.info("Mirror port already set to "
                                                 "mirror something, removing "
                                                 "old mirror setting")
                                del obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch]]['mirror']
            if ok:
                # add mirror to port
                pass
            else:
                self.logger.error("Unable to mirror due to warnings")
                return None
        elif action == 'unmirror':
            pass
        elif action == 'shutdown':
            pass
        else:
            self.logger.warning("Unknown action: " + action)

        document = dump(obj_doc, default_flow_style=False)
        documents[config_file] = document
        self.logger.debug("New configs: " + str(documents))

        return documents

    def log(self, log_file):
        mac_table = {}
        # NOTE very fragile, prone to errors
        with open(log_file, 'r') as f:
            for line in f:
                if 'L2 learned' in line:
                    learned_mac = line.split()
                    data = {'ip-address': learned_mac[16][0:-1],
                            'ip-state': 'L2 learned',
                            'mac': learned_mac[10],
                            'segment': learned_mac[7][1:-1],
                            'port': learned_mac[19],
                            'tenant': learned_mac[21] + learned_mac[22]}
                    if learned_mac[10] in mac_table:
                        dup = False
                        for d in mac_table[learned_mac[10]]:
                            if data == d:
                                dup = True
                        if dup:
                            mac_table[learned_mac[10]].remove(data)
                        mac_table[learned_mac[10]].insert(0, data)
                    else:
                        mac_table[learned_mac[10]] = [data]
        return mac_table

