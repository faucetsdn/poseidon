# -*- coding: utf-8 -*-
"""
Created on 4 March 2020
@author: Charlie Lewis
"""
import logging
import os


class ACL:

    def __init__(self, faucetconfgetsetter):
        self.logger = logging.getLogger('acl')
        self.frpc = faucetconfgetsetter

    def _config_file_paths(self, file_paths):
        return [self.frpc.config_file_path(f) for f in file_paths]

    def include_acl_files(self, rules_doc, rules_file, coprocess_rules_files, obj_doc):
        files = self._config_file_paths(rules_doc['include'])
        rules_path = rules_file.rsplit('/', 1)[0]
        conf_files = obj_doc.get('include', [])

        acls_docs = {}
        for f in files:
            if f.startswith('/'):
                acls_doc = self.frpc.read_faucet_conf(f)
            else:
                acls_doc = self.frpc.read_faucet_conf(
                    os.path.join(rules_path, f))
            if isinstance(acls_doc, bool):
                self.logger.warning(
                    'Include file {0} was not found, ACLs may not be working as expected'.format(f))
                continue
            acls_docs[f] = acls_doc

        if conf_files:
            acls_filenames = []
            if coprocess_rules_files:
                acls_filenames += self._config_file_paths(
                    coprocess_rules_files)
            for f in files:
                if '/' in f:
                    acls_filenames.append(f.rsplit('/', 1)[1])
                else:
                    acls_filenames.append(f)
            for conf_file in conf_files:
                if conf_file.startswith('poseidon') and conf_file not in acls_filenames:
                    obj_doc['include'].remove(conf_file)
                    self.logger.info(
                        'Removing {0} from config'.format(conf_file))
        else:
            obj_doc['include'] = []

        for f, acls_doc in acls_docs.items():
            if '/' in f:
                _, acls_filename = f.rsplit('/', 1)
            else:
                acls_filename = f
            poseidon_acls_filename = 'poseidon_' + acls_filename
            if poseidon_acls_filename not in conf_files:
                obj_doc['include'].append(poseidon_acls_filename)
                self.frpc.write_faucet_conf(os.path.join(
                    rules_path, poseidon_acls_filename), acls_doc)
                self.logger.info('Adding {0} to config'.format(acls_filename))

        # get defined ACL names from included files
        acl_names = []
        for acls_doc in acls_docs.values():
            acl_names.extend(list(acls_doc.get('acls', [])))
        return obj_doc, acl_names

    def match_rules(self, rule, rules, obj_doc, endpoint, switch, port, all_rule_acls, force_apply_rules):
        matches = 0
        for r in rules[rule]:
            if 'rule' in r and 'device_key' in r['rule']:
                rule_data = r['rule']
                if rule_data['device_key'] == 'os':
                    match = False
                    for addresses in ('ipv4_addresses', 'ipv6_addresses'):
                        if 'addresses' in endpoint.metadata:
                            for ip, ip_metadata in endpoint.metadata['addresses']:
                                if 'os' in ip_metadata and ip_metadata['os'] == rule_data['value']:
                                    self.logger.info('{0} os match: {1} {2}, rule: {3}'.format(
                                        addresses, ip, rule_data['value'], rule))
                                    match = True
                    if match:
                        matches += 1
                elif rule_data['device_key'] == 'role':
                    match = False
                    if 'mac_addresses' in endpoint.metadata:
                        for mac, mac_metadata in endpoint.metadata['mac_addresses'].items():
                            most_recent = 0
                            for record in mac_metadata:
                                if float(record) > most_recent:
                                    most_recent = float(record)
                            most_recent = str(most_recent)
                            if most_recent != '0' and most_recent in mac_metadata and 'labels' in mac_metadata[most_recent] and 'confidences' in mac_metadata[most_recent]:
                                # check top three
                                for i in range(3):
                                    if mac_metadata[most_recent]['labels'][i] == rule_data['value']:
                                        if 'min_confidence' in rule_data['value']:
                                            if float(mac_metadata[most_recent]['confidences'][i])*100 >= rule_data['min_confidence']:
                                                self.logger.info('Confidence match: {0} {1}, rule: {2}'.format(mac, float(
                                                    mac_metadata[most_recent]['confidences'][i])*100, rule))
                                                match = True
                                        else:
                                            self.logger.info('Role match: {0} {1}, rule: {2}'.format(
                                                mac, rule_data['value'], rule))
                                            match = True
                    if match:
                        matches += 1
        if matches == len(rules[rule]) or (force_apply_rules and rule in force_apply_rules):
            rule_acls = []
            for r in rules[rule]:
                rule_acls += r['rule']['acls']
                all_rule_acls += r['rule']['acls']
            rule_acls = list(set(rule_acls))
            interfaces_conf = obj_doc['dps'][switch]['interfaces']
            if rule_acls:
                if port not in interfaces_conf:
                    interfaces_conf[port] = {}
            port_conf = interfaces_conf[port]
            if 'acls_in' not in port_conf:
                self.logger.info('All rules met for: {0} on switch: {1} and port: {2}; applying ACLs: {3}'.format(
                    endpoint.endpoint_data['mac'], switch, port, rule_acls))
                port_conf['acls_in'] = rule_acls
            else:
                # add new ACLs
                orig_rule_acls = rule_acls
                rule_acls += port_conf['acls_in']
                rule_acls = list(set(rule_acls))
                if port_conf['acls_in'] != rule_acls:
                    port_conf['acls_in'] = rule_acls
                    self.logger.info('All rules met for: {0} on switch: {1} and port: {2}; applying ACLs: {3}'.format(
                        endpoint.endpoint_data['mac'], switch, port, orig_rule_acls))
        return obj_doc, all_rule_acls

    def apply_acls(self, rules_file, endpoints, force_apply_rules,
                   force_remove_rules, coprocess_rules_files, obj_doc,
                   rules_doc):
        if not endpoints:
            return obj_doc

        # get acls file and add to faucet.yaml if not already there
        if 'include' not in rules_doc:
            self.logger.info(
                'No included ACLs files in the rules file, using ACLs that Faucet already knows about')
        else:
            obj_doc, acl_names = self.include_acl_files(rules_doc, rules_file,
                                                        coprocess_rules_files,
                                                        obj_doc)

        if 'rules' in rules_doc:
            acls = []
            rules = rules_doc['rules']

            for rule in rules:
                for r in rules[rule]:
                    acls += r['rule']['acls']
            acls = list(set(acls))

            # check that acls in rules exist in the included acls file
            if 'include' in rules_doc:
                for acl in acls:
                    if acl not in acl_names:
                        self.logger.info(
                            'Using named ACL: {0}, but it was not found in included ACL files, assuming ACL name exists in Faucet config'.format(acl))

            for endpoint in endpoints:
                port = int(endpoint.endpoint_data['port'])
                switch = endpoint.endpoint_data['segment']
                switch_conf = obj_doc['dps'].get(switch, None)
                if not switch_conf:
                    continue
                port_conf = switch_conf['interfaces'].get(port, None)
                if not port_conf:
                    continue
                existing_acls = port_conf.get('acls_in', None)
                if not existing_acls:
                    continue
                all_rule_acls = []
                for rule in rules:
                    obj_doc, all_rule_acls = self.match_rules(
                        rule, rules, obj_doc, endpoint, switch, port, all_rule_acls, force_apply_rules)
                # remove ACLs that were previously applied
                all_rule_acls = list(set(all_rule_acls))
                for acl in existing_acls:
                    if acl in acls and (acl not in all_rule_acls or acl in force_remove_rules):
                        port_conf['acls_in'].remove(acl)
                        self.logger.info('Removing no longer needed ACL: {0} for: {1} on switch: {2} and port: {3}'.format(
                            acl, endpoint.endpoint_data['mac'], switch, port))

        # TODO acl by port - potentially later update rules in acls to be mac/ip specific
        # TODO ignore trunk ports/stacking ports?

        return obj_doc
