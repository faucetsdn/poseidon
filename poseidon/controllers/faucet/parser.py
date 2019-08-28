# -*- coding: utf-8 -*-
"""
Created on 19 November 2017
@author: Charlie Lewis
"""
import logging
from copy import deepcopy

import yaml

from poseidon.helpers.exception_decor import exception


def represent_none(dumper, _):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')


class Parser:

    def __init__(self,
                 mirror_ports=None,
                 reinvestigation_frequency=None,
                 max_concurrent_reinvestigations=None,
                 ignore_vlans=None):
        self.logger = logging.getLogger('parser')
        self.mirror_ports = mirror_ports
        self.reinvestigation_frequency = reinvestigation_frequency
        self.max_concurrent_reinvestigations = max_concurrent_reinvestigations
        self.ignore_vlans = ignore_vlans

    @staticmethod
    @exception
    def get_config_file(config_file):
        # TODO check for other files
        if not config_file:
            # default to FAUCET default
            config_file = '/etc/faucet/faucet.yaml'
        return config_file

    @staticmethod
    @exception
    def yaml_in(config_file):
        stream = open(config_file, 'r')
        obj_doc = yaml.safe_load(stream)
        stream.close()
        return obj_doc

    @staticmethod
    @exception
    def yaml_out(config_file, obj_doc):
        stream = open(config_file, 'w')
        yaml.add_representer(type(None), represent_none)
        yaml.dump(obj_doc, stream, default_flow_style=False)
        return True

    @staticmethod
    def clear_mirrors(config_file):
        config_file = Parser().get_config_file(config_file)
        obj_doc = Parser().yaml_in(config_file)
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
                return Parser().yaml_out(config_file, obj_doc)
        return False

    @staticmethod
    def parse_rules(config_file):
        config_file = Parser().get_config_file(config_file)
        obj_doc = Parser().yaml_in(config_file)
        return obj_doc

    def config(self, config_file, action, port, switch, rules_file=None, endpoints=None):
        switch_found = None
        config_file = Parser().get_config_file(config_file)
        obj_doc = Parser().yaml_in(config_file)

        if not obj_doc:
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
                    # TODO make this smarter about more complex configurations (backup original values, etc)
                    if self.reinvestigation_frequency:
                        obj_doc['dps'][switch_found]['timeout'] = (
                            self.reinvestigation_frequency * 2) + 1
                    else:
                        obj_doc['dps'][switch_found]['timeout'] = self.reinvestigation_frequency
                    obj_doc['dps'][switch_found]['arp_neighbor_timeout'] = self.reinvestigation_frequency
                    if not port in obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'] and port is not None:
                        obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'].append(
                            port)
                elif action == 'unmirror':
                    try:
                        # TODO check for still running captures on this port
                        obj_doc['dps'][switch_found]['interfaces'][self.mirror_ports[switch_found]]['mirror'].remove(
                            port)
                    except ValueError:
                        self.logger.warning('Port: {0} was not already '
                                            'mirroring on this switch: {1}'.format(str(port), str(switch_found)))
            else:
                self.logger.error('Unable to mirror due to warnings')
                return False
        elif action == 'shutdown':
            # TODO
            pass
        elif action == 'apply_acls':
            if not endpoints:
                return True
            self.logger.info('rules file: {0}'.format(rules_file))
            rules_doc = Parser().parse_rules(rules_file)
            self.logger.info('rules: {0}'.format(rules_doc))
            self.logger.info('faucet config: {0}'.format(obj_doc))
            # TODO get acls file and add to faucet.yaml if not already there - check relative paths, etc.
            if 'include' in rules_doc:
                files = rules_doc['include']
                rules_path = rules_file.rsplit('/', 1)[0]
                config_path = config_file.rsplit('/', 1)[0]
                conf_files = []
                if 'include' in obj_doc:
                    conf_files = obj_doc['include']
                    for conf_file in conf_files:
                        if conf_file.startswith('/'):
                            # absolute
                            # TODO
                            pass
                        else:
                            # relative
                            # TODO
                            pass
                else:
                    # TODO
                    pass
                for f in files:
                    if f.startswith('/'):
                        # absolute
                        # TODO
                        pass
                    else:
                        # relative
                        # TODO
                        pass
            # TODO check that acls in rules exist in the included acls file or already included files/acls from faucet
            if 'rules' in rules_doc:
                acls = []
                rules = rules_doc['rules']

                for rule in rules:
                    for r in rules[rule]:
                        acls += r['rule']['acls']
                acls = list(set(acls))

                for endpoint in endpoints:
                    for rule in rules:
                        matches = 0
                        for r in rules[rule]:
                            if r['rule']['device_key'] == 'os':
                                match = False
                                for ip in endpoint.metadata['ipv4_addresses']:
                                    if 'os' in endpoint.metadata['ipv4_addresses'][ip] and endpoint.metadata['ipv4_addresses'][ip]['os'] == r['rule']['value']:
                                        self.logger.info('ipv4 os match: {0} {1}, rule: {2}'.format(
                                            ip, r['rule']['value'], rule))
                                        match = True
                                for ip in endpoint.metadata['ipv6_addresses']:
                                    if 'os' in endpoint.metadata['ipv6_addresses'][ip] and endpoint.metadata['ipv6_addresses'][ip]['os'] == r['rule']['value']:
                                        self.logger.info('ipv6 os match: {0} {1}, rule: {2}'.format(
                                            ip, r['rule']['value'], rule))
                                        match = True
                                if match:
                                    matches += 1
                            elif r['rule']['device_key'] == 'role':
                                match = False
                                for mac in endpoint.metadata['mac_addresses']:
                                    most_recent = 0
                                    for record in endpoint.metadata['mac_addresses'][mac]:
                                        if float(record) > most_recent:
                                            most_recent = float(record)
                                    most_recent = str(most_recent)
                                    if most_recent != '0' and 'labels' in endpoint.metadata['mac_addresses'][mac][most_recent] and 'confidences' in endpoint.metadata['mac_addresses'][mac][most_recent]:
                                        # check top three
                                        for i in range(3):
                                            if endpoint.metadata['mac_addresses'][mac][most_recent]['labels'][i] == r['rule']['value']:
                                                if 'min_confidence' in r['rule']['value']:
                                                    if float(endpoint.metadata['mac_addresses'][mac][most_recent]['confidences'][i])*100 >= r['rule']['min_confidence']:
                                                        self.logger.info('confidence match: {0} {1}, rule: {2}'.format(mac, float(
                                                            endpoint.metadata['mac_addresses'][mac][most_recent]['confidences'][i])*100, rule))
                                                        match = True
                                                else:
                                                    self.logger.info('role match: {0} {1}, rule: {2}'.format(
                                                        mac, r['rule']['value'], rule))
                                                    match = True
                                if match:
                                    matches += 1
                            elif r['rule']['device_key'] == 'behavior':
                                match = False
                                for mac in endpoint.metadata['mac_addresses']:
                                    most_recent = 0
                                    for record in endpoint.metadata['mac_addresses'][mac]:
                                        if float(record) > most_recent:
                                            most_recent = float(record)
                                    most_recent = str(most_recent)
                                    if most_recent != '0' and 'behavior' in endpoint.metadata['mac_addresses'][mac][most_recent] and endpoint.metadata['mac_addresses'][mac][most_recent]['behavior'] == r['rule']['value']:
                                        self.logger.info('behavior match: {0} {1}, rule: {2}'.format(
                                            mac, r['rule']['value'], rule))
                                        match = True
                                if match:
                                    matches += 1
                        if matches == len(rules[rule]):
                            # TODO only log this when something actually changes, not just matching
                            rule_acls = []
                            for r in rules[rule]:
                                rule_acls += r['rule']['acls']
                            rule_acls = list(set(rule_acls))
                            self.logger.info('all rules met for: {0} on switch: {1} and port: {2}; applying ACLs: {3}'.format(
                                endpoint.endpoint_data['mac'], endpoint.endpoint_data['segment'], endpoint.endpoint_data['port'], rule_acls))
                            if int(endpoint.endpoint_data['port']) not in obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces']:
                                obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                    endpoint.endpoint_data['port'])] = {}
                            if 'acls_in' not in obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(endpoint.endpoint_data['port'])]:
                                obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                    endpoint.endpoint_data['port'])]['acls_in'] = rule_acls
                            else:
                                # TODO check if any changes are necessary first
                                # remove ACLs that were previously applied
                                existing_acls = obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                    endpoint.endpoint_data['port'])]['acls_in']
                                for acl in existing_acls:
                                    if acl in acls:
                                        obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                            endpoint.endpoint_data['port'])]['acls_in'].remove(acl)
                                        self.logger.info('removing no longer needed ACL: {0} for: {1} on switch: {2} and port: {3}'.format(
                                            acl, endpoint.endpoint_data['mac'], endpoint.endpoint_data['segment'], endpoint.endpoint_data['port']))
                                # add new ACLs
                                rule_acls += obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                    endpoint.endpoint_data['port'])]['acls_in']
                                rule_acls = list(set(rule_acls))
                                obj_doc['dps'][endpoint.endpoint_data['segment']]['interfaces'][int(
                                    endpoint.endpoint_data['port'])]['acls_in'] = rule_acls
            else:
                return True

            # TODO check endpoints to see if any of them apply, only change acls on devices that have rules (leave other acls alone)
            # TODO check already applied acls and remove if endpoint no longer applies

            # TODO acl by port - potentially later update rules in acls to be mac/ip specific
            # TODO ignore trunk ports?

            # TODO update faucet.yaml and apply acls
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

        return Parser().yaml_out(config_file, obj_doc)

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
