#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for the Poseidon shell.

Created on 14 January 2019
@author: Charlie Lewis
"""
import csv
import io
import json
import os
import readline
import sys
import time

import cmd2
from natural.date import delta
from natural.date import duration
from texttable import Texttable

from poseidon.cli.commands import Commands
from poseidon.constants import NO_DATA
from poseidon.helpers.exception_decor import exception


readline.parse_and_bind('?: complete')


class GetData():

    @staticmethod
    def _get_name(endpoint):
        return endpoint.machine.name.strip()

    @staticmethod
    def _get_mac(endpoint):
        return endpoint.endpoint_data['mac']

    @staticmethod
    def _get_switch(endpoint):
        return endpoint.endpoint_data['segment']

    @staticmethod
    def _get_port(endpoint):
        return endpoint.endpoint_data['port']

    @staticmethod
    def _get_vlan(endpoint):
        vlan = str(endpoint.endpoint_data['vlan'])
        return vlan.split('VLAN')[1] if vlan.startswith('VLAN') else vlan

    @staticmethod
    def _get_acls(endpoint):
        return str(endpoint.acl_data)

    @staticmethod
    def _get_ipv4(endpoint):
        return str(endpoint.endpoint_data['ipv4'])

    @staticmethod
    def _get_ipv4_subnet(endpoint):
        if 'ipv4_subnet' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv4_subnet'])
        return NO_DATA

    @staticmethod
    def _get_ether_vendor(endpoint):
        if 'ether_vendor' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ether_vendor'])
        return NO_DATA

    @staticmethod
    def _get_ipv4_rdns(endpoint):
        if 'ipv4_rdns' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv4_rdns'])
        return NO_DATA

    @staticmethod
    def _get_ipv6_rdns(endpoint):
        if 'ipv6_rdns' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv6_rdns'])
        return NO_DATA

    @staticmethod
    def _get_ipv6(endpoint):
        return str(endpoint.endpoint_data['ipv6'])

    @staticmethod
    def _get_ipv6_subnet(endpoint):
        if 'ipv6_subnet' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv6_subnet'])
        return NO_DATA

    @staticmethod
    def _get_controller_type(endpoint):
        if 'controller_type' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['controller_type'])
        return NO_DATA

    @staticmethod
    def _get_controller(endpoint):
        if 'controller' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['controller'])
        return NO_DATA

    @staticmethod
    def _get_ignored(endpoint):
        return str(endpoint.ignore)

    @staticmethod
    def _get_state(endpoint):
        return endpoint.state

    @staticmethod
    def _get_next_state(endpoint):
        return str(endpoint.p_next_state)

    @staticmethod
    def _get_first_seen(endpoint):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
            endpoint.p_prev_states[0][1])) + ' (' + duration(endpoint.p_prev_states[0][1]) + ')'

    @staticmethod
    def _get_last_seen(endpoint):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
            endpoint.p_prev_states[-1][1])) + ' (' + duration(endpoint.p_prev_states[-1][1]) + ')'

    @staticmethod
    def _get_role(endpoint):
        result = NO_DATA
        endpoint_mac = GetData._get_mac(endpoint)
        if 'mac_addresses' in endpoint.metadata and endpoint_mac in endpoint.metadata['mac_addresses']:
            metadata = endpoint.metadata['mac_addresses'][endpoint_mac]
            newest = '0'
            for timestamp in metadata:
                if timestamp > newest:
                    newest = timestamp
            if newest is not '0':
                if 'labels' in metadata[newest]:
                    result = metadata[newest]['labels'][0]
        return result

    @staticmethod
    def _get_role_confidence(endpoint):
        result = NO_DATA
        endpoint_mac = GetData._get_mac(endpoint)
        if 'mac_addresses' in endpoint.metadata and endpoint_mac in endpoint.metadata['mac_addresses']:
            metadata = endpoint.metadata['mac_addresses'][endpoint_mac]
            newest = '0'
            for timestamp in metadata:
                if timestamp > newest:
                    newest = timestamp
            if newest is not '0':
                if 'confidences' in metadata[newest]:
                    result = str(metadata[newest]['confidences'][0])
        return result

    @staticmethod
    def _get_ipv4_os(endpoint):
        result = NO_DATA
        endpoint_ip = GetData._get_ipv4(endpoint)
        if 'ipv4_addresses' in endpoint.metadata and endpoint_ip in endpoint.metadata['ipv4_addresses']:
            metadata = endpoint.metadata['ipv4_addresses'][endpoint_ip]
            if 'os' in metadata:
                result = metadata['os']
        return result

    @staticmethod
    def _get_ipv6_os(endpoint):
        result = NO_DATA
        endpoint_ip = GetData._get_ipv6(endpoint)
        if 'ipv6_addresses' in endpoint.metadata and endpoint_ip in endpoint.metadata['ipv6_addresses']:
            metadata = endpoint.metadata['ipv6_addresses'][endpoint_ip]
            if 'os' in metadata:
                result = metadata['os']
        return result

    @staticmethod
    def _get_behavior(endpoint):
        result = NO_DATA
        endpoint_mac = GetData._get_mac(endpoint)
        if 'mac_addresses' in endpoint.metadata and endpoint_mac in endpoint.metadata['mac_addresses']:
            metadata = endpoint.metadata['mac_addresses'][endpoint_mac]
            newest = '0'
            for timestamp in metadata:
                if timestamp > newest:
                    newest = timestamp
            if newest is not '0':
                if 'behavior' in metadata[newest]:
                    result = metadata[newest]['behavior']
        return result

    @staticmethod
    def _get_prev_roles(endpoint):
        # TODO results from ML
        return

    @staticmethod
    def _get_prev_role_confidences(endpoint):
        # TODO results from ML
        return

    @staticmethod
    def _get_prev_behaviors(endpoint):
        # TODO results from ML
        return

    @staticmethod
    def _get_prev_ipv4_oses(endpoint):
        # TODO results from p0f
        return

    @staticmethod
    def _get_prev_ipv6_oses(endpoint):
        # TODO results from p0f
        return

    @staticmethod
    def _get_prev_states(endpoint):
        prev_states = endpoint.p_prev_states
        oldest_state = []
        output = NO_DATA
        if len(prev_states) > 1:
            oldest_state = prev_states.pop(0)
            current_state = prev_states.pop()
        elif len(prev_states) == 1:
            current_state = oldest_state = prev_states.pop()
        else:
            return output

        output = 'First seen: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
            oldest_state[1])) + ' (' + duration(oldest_state[1]) + ') and put into state: ' + oldest_state[0] + '\n'
        last_state = oldest_state
        for state in prev_states:
            delay = delta(state[1], last_state[1])[0]
            if delay == 'just now':
                delay = 'immediately'
            else:
                delay += ' later'
            output += 'then ' + delay + ' it changed into state: ' + state[0] + \
                ' (' + time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.localtime(state[1])) + ')\n'
            last_state = state
        output += 'Finally it was last seen: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
            current_state[1])) + ' (' + duration(current_state[1]) + ')'
        return output

    @staticmethod
    def _get_history(endpoint):
        hist = ''
        if len(endpoint.history) > 0:
            for entry in endpoint.history:
                hist += '{0} - {1} : {2} \r\n'.format(entry['type'], time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp'])), entry['message'])
        else:
            hist = 'No history recorded yet.'
        return hist


class Parser():

    def __init__(self):
        self.default_fields = [
            'IPv4', 'IPv4 rDNS', 'Role', 'IPv4 OS', 'Ethernet Vendor',
            'MAC Address'
        ]
        self.all_fields = [
            'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4',
            'IPv4 Subnet', 'IPv6', 'IPv6 Subnet', 'Ethernet Vendor', 'Ignored',
            'State', 'Next State', 'First Seen', 'Last Seen',
            'Previous States', 'IPv4 OS\n(p0f)', 'IPv6 OS\n(p0f)', 'Previous IPv4 OSes\n(p0f)',
            'Previous IPv6 OSes\n(p0f)', 'Role\n(NetworkML)', 'Role Confidence\n(NetworkML)', 'Previous Roles\n(NetworkML)',
            'Previous Role Confidences\n(NetworkML)', 'Behavior\n(NetworkML)', 'Previous Behaviors\n(NetworkML)',
            'IPv4 rDNS', 'IPv6 rDNS', 'SDN Controller Type', 'SDN Controller URI', 'History', 'ACL History',
        ]

    def completion(self, text, line, completions):
        firstword, _, mline = line.partition(' ')
        offs = len(mline) - len(text)
        words = []

        completes = [s[offs:]
                     for s in completions if s.lower().startswith(mline.lower())]
        for complete in completes:
            words.append(complete.split(' ', 1)[0])
        return words

    def get_flags(self, text):
        valid = True
        flags = {}
        not_flags = []
        # remove boolean flags first
        words = text.split()
        other_words = []
        for word in words:
            if len(word) > 1 and word[0] == '-' and word[1] != '-':
                flags[word[1:]] = True
            else:
                other_words.append(word)
        other_words = ' '.join(other_words)
        first = other_words.split('--')
        not_flags += first[0].split()
        first.pop(0)
        for flag in first:
            if '=' in flag:
                command, value = flag.split('=', 1)
                if '[' in value and ']' in value:
                    val = value.rsplit(']', 1)[0].split('[', 1)[1]
                    val = val.split(',')
                    store_vals = []
                    for v in val:
                        store_vals.append(v.strip())
                    flags[command] = store_vals
                    not_f = value.rsplit(']', 1)
                else:
                    val = value.split(' ', 1)[0]
                    flags[command] = val
                    not_f = value.split(' ', 1)
                not_f.pop(0)
                if not_f:
                    not_flags += not_f[0].split()
            else:
                valid = False
        return valid, flags, ' '.join(not_flags)

    def _check_flags(self, flags, fields, sort_by=0, max_width=0, unique=False, nonzero=False, output_format='table', ipv4_only=True, ipv6_only=False, ipv4_and_ipv6=False):
        valid = True
        for flag in flags:
            if flag == 'fields':
                # TODO better validation and error checking needed
                if 'all' in flags[flag]:
                    fields = self.all_fields
                else:
                    fields = flags[flag]
            elif flag == 'sort_by':
                sort_by = int(flags[flag])
            elif flag == 'max_width':
                max_width = int(flags[flag])
            elif flag == 'unique' and flags[flag] == True:
                unique = True
            elif flag == 'nonzero' and flags[flag] == True:
                nonzero = True
            elif flag == 'output_format':
                output_format = flags[flag]
            elif flag == '4' and flags[flag] == True:
                ipv4_only = True
                ipv6_only = False
                ipv4_and_ipv6 = False
            elif flag == '6' and flags[flag] == True:
                ipv6_only = True
                ipv4_only = False
                ipv4_and_ipv6 = False
            elif flag == '4and6' and flags[flag] == True:
                ipv4_only = False
                ipv6_only = False
                ipv4_and_ipv6 = True
            else:
                valid = False

        if 'fields' in flags and not '4' in flags and not '6' in flags and not '4and6' in flags:
            ipv4_only = False
            ipv6_only = False
            ipv4_and_ipv6 = False

        return valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6

    @staticmethod
    def display_ip_filter(fields, ipv4_only, ipv6_only, ipv4_and_ipv6):
        if not ipv4_only and not ipv6_only and not ipv4_and_ipv6:
            return fields
        IPV4_FIELD = 'ipv4'
        IPV6_FIELD = 'ipv6'
        IP_FIELDS = {IPV4_FIELD, IPV6_FIELD}
        filtered_fields = []
        ip_fields_filter = set()
        if ipv4_only or ipv4_and_ipv6:
            ip_fields_filter.add(IPV4_FIELD)
        if ipv6_only or ipv4_and_ipv6:
            ip_fields_filter.add(IPV6_FIELD)
        for field in fields:
            ip_fields = {ip_field for ip_field in IP_FIELDS if ip_field in field.lower()}
            if ip_fields and not ip_fields.issubset(ip_fields_filter):
                continue
            filtered_fields.append(field)
        return filtered_fields

    def display_results(self, endpoints, fields, sort_by=0, max_width=0, unique=False, nonzero=False, output_format='table', ipv4_only=True, ipv6_only=False, ipv4_and_ipv6=False):
        matrix = []
        fields = self.display_ip_filter(fields, ipv4_only, ipv6_only, ipv4_and_ipv6)
        fields_lookup = {'id': (GetData._get_name, 0),
                         'mac': (GetData._get_mac, 1),
                         'mac address': (GetData._get_mac, 1),
                         'switch': (GetData._get_switch, 2),
                         'port': (GetData._get_port, 3),
                         'vlan': (GetData._get_vlan, 4),
                         'ipv4': (GetData._get_ipv4, 5),
                         'ipv4 subnet': (GetData._get_ipv4_subnet, 6),
                         'ipv6': (GetData._get_ipv6, 7),
                         'ipv6 subnet': (GetData._get_ipv6_subnet, 8),
                         'ethernet vendor': (GetData._get_ether_vendor, 9),
                         'ignored': (GetData._get_ignored, 10),
                         'state': (GetData._get_state, 11),
                         'next state': (GetData._get_next_state, 12),
                         'first seen': (GetData._get_first_seen, 13),
                         'last seen': (GetData._get_last_seen, 14),
                         'previous states': (GetData._get_prev_states, 15),
                         'ipv4 os': (GetData._get_ipv4_os, 16),
                         'ipv4 os\n(p0f)': (GetData._get_ipv4_os, 16),
                         'ipv6 os': (GetData._get_ipv6_os, 17),
                         'ipv6 os\n(p0f)': (GetData._get_ipv6_os, 17),
                         'previous ipv4 oses': (GetData._get_prev_ipv4_oses, 18),
                         'previous ipv4 oses\n(p0f)': (GetData._get_prev_ipv4_oses, 18),
                         'previous ipv6 oses': (GetData._get_prev_ipv6_oses, 19),
                         'previous ipv6 oses\n(p0f)': (GetData._get_prev_ipv6_oses, 19),
                         'role': (GetData._get_role, 20),
                         'role\n(networkml)': (GetData._get_role, 20),
                         'role confidence': (GetData._get_role_confidence, 21),
                         'role confidence\n(networkml)': (GetData._get_role_confidence, 21),
                         'previous roles': (GetData._get_prev_roles, 22),
                         'previous roles\n(networkml)': (GetData._get_prev_roles, 22),
                         'previous role confidences': (GetData._get_prev_role_confidences, 23),
                         'previous role confidences\n(networkml)': (GetData._get_prev_role_confidences, 23),
                         'behavior': (GetData._get_behavior, 24),
                         'behavior\n(networkml)': (GetData._get_behavior, 24),
                         'previous behaviors': (GetData._get_prev_behaviors, 25),
                         'previous behaviors\n(networkml)': (GetData._get_prev_behaviors, 25),
                         'ipv4 rdns': (GetData._get_ipv4_rdns, 26),
                         'ipv6 rdns': (GetData._get_ipv6_rdns, 27),
                         'sdn controller type': (GetData._get_controller_type, 28),
                         'sdn controller uri': (GetData._get_controller, 29),
                         'history': (GetData._get_history, 30),
                         'acl history': (GetData._get_acls, 31)}

        records = []
        if nonzero or unique:
            raw_records = []
            all_fields_with_data = set()

            for endpoint in endpoints:
                raw_record = {
                    field: fields_lookup[field.lower()][0](endpoint)
                    for field in fields}
                fields_with_data = {
                    field for field, value in raw_record.items() if value and value != NO_DATA}
                all_fields_with_data.update(fields_with_data)
                # remove rows that are all zero or 'NO DATA'
                if fields_with_data:
                    raw_records.append(raw_record)

            # delete columns with no data
            all_fields_with_no_data = set(fields) - all_fields_with_data
            fields = [field for field in fields if field in all_fields_with_data]
            for raw_record in raw_records:
                for field in all_fields_with_no_data:
                    del raw_record[field]
                records.append([raw_record[field] for field in fields])

            if len(fields) > 0:
                if unique:
                    u_records = set(map(tuple, records))
                    records = list(u_records)
                    matrix = list(map(list, u_records))
                else:
                    matrix = records
        if not nonzero and not unique:
            for endpoint in endpoints:
                record = []
                for field in fields:
                    if field.lower() in fields_lookup:
                        record.append(fields_lookup[field.lower()][0](endpoint))
                        records.append(record)
                matrix.append(record)
        results = ''
        if output_format == 'json':
            results = json.dumps(records, indent='\t')
        elif len(matrix) > 0:
            matrix = sorted(matrix, key=lambda endpoint: endpoint[sort_by])
            # swap out field names for header
            fields_header = []
            for field in fields:
                fields_header.append(
                    self.all_fields[fields_lookup[field.lower()][1]])
            # set the header
            matrix.insert(0, fields_header)
            if output_format == 'csv':
                results = self.display_csv(matrix)
            else:
                results = self.display_table(len(fields), max_width, matrix)
        else:
            results = 'No results found for that query.'
        return results

    def display_table(self, column_count, max_width, matrix):
        table = Texttable(max_width=max_width)
        # make all the column types be text
        table.set_cols_dtype(['t']*column_count)
        table.add_rows(matrix)
        return table.draw()

    def display_csv(self, matrix):
        # use StringIO to create a file like object as a string so that we can use the
        # built in csv contructs so as to properly handle edge/corner cases
        csv_str = io.StringIO()
        csv_wr = csv.writer(csv_str)
        for row in matrix:
            csv_wr.writerow(row)

        return csv_str.getvalue()


class PoseidonShell(cmd2.Cmd):

    def __init__(self, *args, **kwargs):
        super().__init__(persistent_history_file='/opt/poseidon/.poseidon_history', *args, **kwargs)
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_py
        del cmd2.Cmd.do_run_pyscript

        self.parser = Parser()
        self.intro = """Welcome to the Poseidon shell. Type 'help' to list commands.
<TAB> or '?' will autocomplete commands.
                               _      \033[1;31m__\033[1;m
    ____   ____   \033[1;31m_____\033[1;m ___   (_)\033[1;31m____/ /\033[1;m____   \033[1;31m____\033[1;m
   / __ \ / __ \ \033[1;31m/ ___/\033[1;m/ _ \ / /\033[1;31m/ __  /\033[1;m/ __ \ \033[1;31m/ __ \\\033[1;m
  / /_/ // /_/ /\033[1;31m(__  )\033[1;m/  __// /\033[1;31m/ /_/ /\033[1;m/ /_/ /\033[1;31m/ / / /\033[1;m
 / .___/ \____/\033[1;31m/____/\033[1;m \___//_/ \033[1;31m\__,_/\033[1;m \____/\033[1;31m/_/ /_/\033[1;m
/_/\n"""
        self.prompt = '\033[1;32mposeidon$ \033[1;m'

        self.show_completions = [
            'role active-directory-controller', 'role administrator-server',
            'role administrator-workstation', 'role business-workstation',
            'role developer-workstation', 'role gpu-laptop', 'role pki-server',
            'role unknown', 'state active', 'state inactive', 'state known',
            'state unknown', 'state mirroring', 'state abnormal', 'state shutdown',
            'state reinvestigating', 'state queued', 'state ignored',
            'behavior normal', 'behavior abnormal', 'os windows', 'os freebsd',
            'os linux', 'os mac', 'history', 'version', 'what', 'where', 'all'
        ]

        self.task_completions = [
            'set', 'ignore', 'remove', 'collect', 'clear'
        ]

    def complete_show(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.show_completions)

    def complete_task(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.task_completions)

    @exception
    def show_all(self, arg, flags):
        '''Show all things on the network'''
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().show_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_role(self, arg, flags):
        '''Show all things on the network that match a role'''
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().show_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_state(self, arg, flags):
        '''Show all things on the network that match a state'''
        fields = ['Switch', 'Port', 'State',
                  'Ethernet Vendor', 'Mac', 'IPv4', 'IPv6']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields, ipv4_only=False)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().show_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_behavior(self, arg, flags):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields + ['Behavior']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().show_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_os(self, arg, flags):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().show_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_what(self, arg, flags):
        '''
        Find out what something is:
        WHAT [IP|MAC|ID]
        WHAT 10.0.0.1
        WHAT 18:EF:02:2D:49:00
        WHAT 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = self.parser.all_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().what_is(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_history(self, arg, flags):
        '''
        Find out the history of something on the network:
        HISTORY [IP|MAC|ID]
        HISTORY 10.0.0.1
        HISTORY 18:EF:02:2D:49:00
        HISTORY 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['History']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().history_of(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_acls(self, arg, flags):
        '''
        Find out the history of ACLs of something on the network:
        ACLS [IP|MAC|ID]
        ACLS 10.0.0.1
        ACLS 18:EF:02:2D:49:00
        ACLS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['ACL History']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().acls_of(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def show_where(self, arg, flags):
        '''
        Find out where something is:
        WHERE [IP|MAC|ID]
        WHERE 10.0.0.1
        WHERE 18:EF:02:2D:49:00
        WHERE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['Switch', 'Port', 'VLAN', 'IPv4', 'IPv6', 'MAC Address']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields, ipv4_only=False)

        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            self.poutput(self.parser.display_results(Commands().where_is(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def help_show(self):
        self.poutput('  acls\t\tShow ACL history of something on the network')
        self.poutput('  all\t\tShow all devices')
        self.poutput('  behavior\tShow devices matching a particular behavior')
        self.poutput(
            '  history\tFind out the history of something on the network')
        self.poutput(
            '  os\t\tShow devices matching a particular operating system')
        self.poutput('  role\t\tShow devices matching a particular role')
        self.poutput('  state\t\tShow devices matching a particular state')
        self.poutput('  version\tShow the version of Poseidon running')
        self.poutput('  what\t\tFind out what something is')
        self.poutput('  where\t\tFind out where something is')

    @exception
    def show_authors(self, arg, flags):
        self.poutput("""\033[1;34m                            The Cyber Reboot Team
                                      &
                           Members of the Community\033[1;m
                           \033[1;31m`-:/+oosyyyyyyyysso+/:-`
                      .:+oyyyyyyyyyyyyyyyyyyyyyyyyyyo+:.
                  `:+yyyyyyyyyyyyyyyyyssyyyyyyyyyyyyyyyyy+:`
               `:oyyyyyyyyyyo+/:-.`        `.-:/+oyyyyyyyyyyo:`
             -+yyyyyyyys+:.                        .:+syyyyyyyy+-
           -oyyyyyyyo:.                                .:oyyyyyyys-
         -oyyyyyys/.                                      `/syyyyyys-
       `+yyyyyys:`              `.--::::::--.`              `-oyyyyyy+`     ``
      -syyyyys:            `-/osyyyyyyyyyyyyyys+/-`            :syyyyys-  -syys:
     /yyyyyy+`          ./oyyyyyyyyyyyyyyyyyyyyyyyyo:.          `/yyyyyy/.yyyyys
    /yyyyyy-         `-oyyyyyyyyyyyyyysoyyyyyyyyyyyyyyo-      -/+/+yyyyyyyyyyyy:
   /yyyyys.         :syyyyyyyyyyyyyyyy/`yyyyyyyyyyyyyyyyo-   -yyyyyyyyyyyyyyyyo
  :yyyyys.        .oyyyyyyyyys+syyyyyy: yyyyyyy+oyyyyyyyyy+` .syyyyyyyyyyyyyyy`
 `yyyyyy.        -syyyyyyyyo:.:syyyyyy: yyyyyyy/-.+yyyyyyyys- `./oyyyyyyyyyyy:
 +yyyyy/        :yyyyyyyys:./syyyyyyyy: yyyyyyyyyo-.+yyyyyyyy-    `:+syyyyyyo
`yyyyys`       -yyyyyyyyo.-syyyyyyyyyy: yyyyyyyyyyy+`/yyyyyyyy.      `./osyy`
/yyyyy/       `syyyyyyys`-yyyyyyyyyyyy: yyyyyyyyyyyyo`:yyyyyyyo          `--
oyyyyy.       :yyyyyyyy-`yyyyyyyyyyyyy: yyyyyyyyyyyyy/ oyyyyyyy-
syyyyy        oyyyyyyys /yyyyyyyyyyyyy: yyyyyyyyyyyyyy`-yyyyyyy+
yyyyyy        syyyyyyy+ oyyyyyyyyyyyyy: yyyyyyyyyyyyyy..yyyyyyyo
yyyyyy        syyyyyyyo +yyyyyyyyyyyyy/`yyyyyyyyyyyyyy`.yyyyyyyo
oyyyyy.       oyyyyyyyy`-yyyyyyyyyyyyyysyyyyyyyyyyyyyo /yyyyyyy/
/yyyyy/       :yyyyyyyy/ +yyyyyyyyyyyyyyyyyyyyyyyyyyy..yyyyyyyy.
`yyyyys`       syyyyyyyy:`+yyyyyyyyyyyyyyyyyyyyyyyys-`syyyyyyyo        :+o+:
 +yyyyy/       .yyyyyyyyy+`:syyyyyyyyyyyyyyyyyyyyy+.-syyyyyyys.       /yyyyy-
 `yyyyyy-       :yyyyyyyyys:.:syyyyyyyyyyyyyyyys+-.+yyyyyyyyy-       .yyyyyy`
  :yyyyys.       -syyyyyyyyys/.-:+ssyyyyyysso/:.:oyyyyyyyyys.       .syyyyy:
   /yyyyys.       `oyyyyyyyyyyys+:----------:/oyyyyyyyyyyy+`       .syyyyy/
    /yyyyyy-        -oyyyyyyyyyyyyyyyssssyyyyyyyyyyyyyyyo-        -yyyyyy/
     :yyyyyy+`        -oyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy+-        `+yyyyyy/
      -syyyyys:         .:oyyyyyyyyyyyyyyyyyyyyyyyso:`        `:syyyyys-
       `+yyyyyys:`         `-/+syyyyyyyyyyyyyys+:-`         `:syyyyyy+`
         -oyyyyyys/.            `..--::::--.`             ./syyyyyyo-
           -oyyyyyyyo/.                                .:oyyyyyyyo-
             -+yyyyyyyys+:.                        .:+syyyyyyyy+-
               `:oyyyyyyyyyyo+/:-.``      ``.-:/+oyyyyyyyyyyo:`
                  `:+yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyys+:`
                      .:/oyyyyyyyyyyyyyyyyyyyyyyyyyyo+:.
                           `-:/+oossyyyyyyssoo+/:-`\033[1;m""")
        with open('/poseidon/AUTHORS', 'r') as f:  # pragma: no cover
            i = 1
            for line in f:
                if i > 4:
                    self.poutput(line.strip())
                i += 1

    @exception
    def show_version(self, arg, flags):
        with open('/poseidon/VERSION', 'r') as f:  # pragma: no cover
            for line in f:
                self.poutput(line.strip())

    @exception
    def task_set(self, arg, flags):
        '''
        Set the state of things on the network:
        SET [IP|MAC|ID] [STATE]
        SET 10.0.0.1 INACTIVE
        SET ABNORMAL UNKNOWN (TODO - NOT IMPLEMENTED YET)
        SET 18:EF:02:2D:49:00 KNOWN
        SET 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293 SHUTDOWN
        '''
        # defaults
        fields = self.parser.default_fields + ['State', 'Next State']

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help task'")
        else:
            self.poutput('Set the following device states:')
            self.poutput(self.parser.display_results(Commands().change_devices(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def task_collect(self, arg, flags):
        '''
        Collect on something on the network for a duration:
        COLLECT [IP|MAC|ID] [DURATION] (TODO - NOT IMPLEMENTED YET)
        '''
        # TODO
        self.poutput('Not implemented yet')

    @exception
    def task_ignore(self, arg, flags):
        '''
        Ignore something on the network:
        IGNORE [IP|MAC|ID]
        IGNORE 10.0.0.1
        IGNORE 18:EF:02:2D:49:00
        IGNORE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        IGNORE INACTIVE
        '''
        # defaults
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help task'")
        else:
            self.poutput('Ignored the following devices:')
            self.poutput(self.parser.display_results(Commands().ignore(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def task_clear(self, arg, flags):
        '''
        Stop ignoring something on the network:
        CLEAR [IP|MAC|ID]
        CLEAR 10.0.0.1
        CLEAR 18:EF:02:2D:49:00
        CLEAR 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        CLEAR IGNORED
        '''
        # defaults
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help task'")
        else:
            self.poutput(
                'Cleared the following devices that were being ignored:')
            self.poutput(self.parser.display_results(Commands().clear_ignored(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def task_remove(self, arg, flags):
        '''
        Remove something on the network until it's seen again:
        REMOVE [IP|MAC|ID]
        REMOVE 10.0.0.1
        REMOVE 18:EF:02:2D:49:00
        REMOVE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        REMOVE IGNORED
        REMOVE INACTIVE
        '''
        # defaults
        fields = self.parser.default_fields

        valid, fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        if not valid:
            self.poutput("Unknown flag, try 'help task'")
        else:
            endpoints = []
            if arg.startswith('ignored'):
                endpoints = Commands().remove_ignored(arg)
            elif arg.startswith('inactive'):
                endpoints = Commands().remove_inactives(arg)
            else:
                endpoints = Commands().remove(arg)
            self.poutput('Removed the following devices:')
            self.poutput(self.parser.display_results(endpoints, fields, sort_by=sort_by, max_width=max_width, unique=unique,
                                                     nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6))

    @exception
    def help_task(self):
        self.poutput('  clear\t\tStop ignoring something on the network')
        self.poutput(
            '  collect\tCollect on something on the network for a duration')
        self.poutput('  ignore\tIgnore something on the network')
        self.poutput(
            '  remove\tRemove something on the network until it is seen again')
        self.poutput('  set\t\tSet the state of things on the network')

    @exception
    def do_task(self, arg):
        '''Perform task to things on the network'''
        valid, flags, arg = self.parser.get_flags(arg)
        if not valid:
            self.poutput("Unknown flag, try 'help task'")
        else:
            if arg:
                action = arg.split()[0]
                func_calls = {'clear': self.task_clear,
                              'collect': self.task_collect,
                              'ignore': self.task_ignore,
                              'remove': self.task_remove,
                              'set': self.task_set}
                if action in func_calls:
                    if len(arg.split()) > 1:
                        func_calls[action](arg, flags)
                    else:
                        self.poutput(action.upper() + ' <ID|IP|MAC>')
                else:
                    self.poutput("Unknown command, try 'help task'")
            else:
                self.help_task()

    @exception
    def do_show(self, arg):
        '''Show things on the network based on filters'''
        valid, flags, arg = self.parser.get_flags(arg)
        if not valid:
            self.poutput("Unknown flag, try 'help show'")
        else:
            if arg:
                action = arg.split()[0]
                func_calls = {'acls': self.show_acls,
                              'all': self.show_all,
                              'authors': self.show_authors,
                              'behavior': self.show_behavior,
                              'history': self.show_history,
                              'os': self.show_os,
                              'role': self.show_role,
                              'state': self.show_state,
                              'version': self.show_version,
                              'what': self.show_what,
                              'where': self.show_where}
                if action in func_calls:
                    if action in ['all', 'authors', 'version']:
                        func_calls[action](arg, flags)
                    elif action in ['acl', 'history', 'what', 'where']:
                        if len(arg.split()) > 1:
                            func_calls[action](arg, flags)
                        else:
                            self.poutput(action.upper() + ' <ID|IP|MAC>')
                    else:
                        valid = False
                        for show_comm in self.show_completions:
                            if arg.startswith(show_comm):
                                valid = True
                                func_calls[action](arg, flags)
                        if not valid:
                            self.poutput("Unknown command, try 'help show'")
                else:
                    self.poutput("Unknown command, try 'help show'")
            else:
                self.help_show()

    @exception
    def do_quit(self, arg):
        '''Stop the shell and exit:  QUIT'''
        self.poutput('Thank you for using Poseidon')
        return True

    @exception
    def do_exit(self, arg):
        '''Stop the shell and exit:  EXIT'''
        self.poutput('Thank you for using Poseidon')
        return True

    @exception
    def do_help(self, arg):
        if not arg:
            self.poutput('For help on specific commands: help <command>')
            self.poutput('Commands:')
            self.poutput('  alias\t\t\tReplace a command with another string')
            self.poutput('  exit\t\t\tStop the shell and exit')
            self.poutput(
                '  fields\t\tList out all available field names - TO BE IMPLEMENTED')
            self.poutput('  history\t\tHistory of commands from this session')
            self.poutput('  load\t\t\tLoad a file of commands to execute')
            self.poutput(
                '  macro\t\t\tSimilar to an alias, but it can contain argument placeholders')
            self.poutput('  quit\t\t\tStop the shell and exit')
            self.poutput(
                '  set\t\t\tApply settings for all future commands in this session - TO BE IMPLEMENTED')
            self.poutput(
                '  shell\t\t\tExecutes commands on the shell inside the Poseidon container')
            self.poutput('  shortcuts\t\tShow existing shortcuts for commands')
            self.poutput(
                '  show\t\t\tShow things on the network based on filters')
            self.poutput('  task\t\t\tPerform a task on things on the network')
            self.poutput('\n')
            self.poutput('Optional flags that can be combined with commands:')
            self.poutput(
                '  --fields\t\tSpecify which fields to display, i.e. --fields=[id, mac]')
            self.poutput(
                '  --max_width\t\tSpecify a max width of characters for output, i.e. --max_width=80')
            self.poutput(
                '  --output_format\tValid values are table, csv, and json')
            self.poutput(
                '  --sort_by\t\tSort the output by a specific column index, i.e. --sort_by=0')
            self.poutput('\n')
            self.poutput('Boolean flags that can be combined with commands:')
            self.poutput('  -4and6\t\tShow fields for both IPv4 and IPv6')
            self.poutput('  -4\t\t\tShow only IPv4 fields')
            self.poutput('  -6\t\t\tShow only IPv6 fields')
            self.poutput(
                '  -nonzero\t\tRemoves rows and columns that contain only "0"s or "NO DATA"')
            self.poutput(
                '  -unique\t\tRemoves columns that all contain the same value')
        else:
            cmd2.Cmd.do_help(self, arg)

    @exception
    def do_set(self, arg):
        comm = arg.partition(' ')[0]
        if comm in ['colors', 'debug', 'echo', 'prompt', 'timing']:
            cmd2.Cmd.do_set(self, arg)
        else:
            self.poutput('TO DO')

    def emptyline(self):
        pass

    @exception
    def do_shell(self, s):
        '''Execute shell commands inside the Poseidon container'''
        os.system(s)


if __name__ == '__main__':  # pragma: no cover
    p_shell = PoseidonShell()
    if '-c' in sys.argv:
        while sys.argv.pop(0) != '-c':
            pass
        p_shell.onecmd(' '.join(sys.argv))
    else:
        p_shell.cmdloop()
