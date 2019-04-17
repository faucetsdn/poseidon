#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for the Poseidon shell.

Created on 14 January 2019
@author: Charlie Lewis
"""
import os
import readline
import time

import cmd2 as cmd
from natural.date import delta
from natural.date import duration
from texttable import Texttable

from poseidon.cli.commands import Commands
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
        vlan = endpoint.endpoint_data['tenant']
        return vlan.split('VLAN')[1] if vlan.startswith('VLAN') else vlan

    @staticmethod
    def _get_ipv4(endpoint):
        return str(endpoint.endpoint_data['ipv4'])

    @staticmethod
    def _get_ipv4_subnet(endpoint):
        if 'ipv4_subnet' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv4_subnet'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_ether_vendor(endpoint):
        if 'ether_vendor' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ether_vendor'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_ipv4_rdns(endpoint):
        if 'ipv4_rdns' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv4_rdns'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_ipv6_rdns(endpoint):
        if 'ipv6_rdns' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv6_rdns'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_ipv6(endpoint):
        return str(endpoint.endpoint_data['ipv6'])

    @staticmethod
    def _get_ipv6_subnet(endpoint):
        if 'ipv6_subnet' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['ipv6_subnet'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_controller_type(endpoint):
        if 'controller_type' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['controller_type'])
        else:
            return 'NO DATA'

    @staticmethod
    def _get_controller(endpoint):
        if 'controller' in endpoint.endpoint_data:
            return str(endpoint.endpoint_data['controller'])
        else:
            return 'NO DATA'

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
        result = 'NO DATA'
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
        result = 'NO DATA'
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
        result = 'NO DATA'
        endpoint_ip = GetData._get_ipv4(endpoint)
        if 'ipv4_addresses' in endpoint.metadata and endpoint_ip in endpoint.metadata['ipv4_addresses']:
            metadata = endpoint.metadata['ipv4_addresses'][endpoint_ip]
            if 'os' in metadata:
                result = metadata['os']
        return result

    @staticmethod
    def _get_ipv6_os(endpoint):
        result = 'NO DATA'
        endpoint_ip = GetData._get_ipv6(endpoint)
        if 'ipv6_addresses' in endpoint.metadata and endpoint_ip in endpoint.metadata['ipv6_addresses']:
            metadata = endpoint.metadata['ipv6_addresses'][endpoint_ip]
            if 'os' in metadata:
                result = metadata['os']
        return result

    @staticmethod
    def _get_behavior(endpoint):
        result = 'NO DATA'
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
        output = 'NO DATA'
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
            'Previous IPv6 OSes\n(p0f)', 'Role\n(PoseidonML)', 'Role Confidence\n(PoseidonML)', 'Previous Roles\n(PoseidonML)',
            'Previous Role Confidences\n(PoseidonML)', 'Behavior\n(PoseidonML)', 'Previous Behaviors\n(PoseidonML)',
            'IPv4 rDNS', 'IPv6 rDNS', 'SDN Controller Type', 'SDN Controller URI'
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
        return flags, ' '.join(not_flags)

    def _check_flags(self, flags, fields, sort_by=0, max_width=0, unique=False, nonzero=False, output_format='table', ipv4_only=True, ipv6_only=False, ipv4_and_ipv6=False):
        for flag in flags:
            if flag == 'fields':
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

        if 'fields' in flags and not '4' in flags and not '6' in flags and not '4and6' in flags:
            ipv4_only = False
            ipv6_only = False
            ipv4_and_ipv6 = False

        return fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6

    def display_results(self, endpoints, fields, sort_by=0, max_width=0, unique=False, nonzero=False, output_format='table', ipv4_only=True, ipv6_only=False, ipv4_and_ipv6=False):
        matrix = []
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
                         'role\n(poseidonml)': (GetData._get_role, 20),
                         'role confidence': (GetData._get_role_confidence, 21),
                         'role confidence\n(poseidonml)': (GetData._get_role_confidence, 21),
                         'previous roles': (GetData._get_prev_roles, 22),
                         'previous roles\n(poseidonml)': (GetData._get_prev_roles, 22),
                         'previous role confidences': (GetData._get_prev_role_confidences, 23),
                         'previous role confidences\n(poseidonml)': (GetData._get_prev_role_confidences, 23),
                         'behavior': (GetData._get_behavior, 24),
                         'behavior\n(poseidonml)': (GetData._get_behavior, 24),
                         'previous behaviors': (GetData._get_prev_behaviors, 25),
                         'previous behaviors\n(poseidonml)': (GetData._get_prev_behaviors, 25),
                         'ipv4 rdns': (GetData._get_ipv4_rdns, 26),
                         'ipv6 rdns': (GetData._get_ipv6_rdns, 27),
                         'sdn controller type': (GetData._get_controller_type, 28),
                         'sdn controller uri': (GetData._get_controller, 29)}
        for index, field in enumerate(fields):
            if ipv4_only:
                if '6' in field:
                    fields[index] = field.replace('6', '4')
            if ipv6_only:
                if '4' in field:
                    fields[index] = field.replace('4', '6')
        if ipv4_and_ipv6:
            for index, field in enumerate(fields):
                if '4' in field:
                    if field.replace('4', '6') not in fields:
                        fields.insert(index + 1, field.replace('4', '6'))
                if '6' in field:
                    if field.replace('6', '4') not in fields:
                        fields.insert(index + 1, field.replace('6', '4'))

        if nonzero or unique:
            records = []
            for endpoint in endpoints:
                record = []
                for field in fields:
                    record.append(fields_lookup[field.lower()][0](endpoint))
                # remove rows that are all zero or 'NO DATA'
                if not nonzero or not all(item == '0' or item == 'NO DATA' for item in record):
                    records.append(record)

            # remove columns that are all zero or 'NO DATA'
            del_columns = []
            for i in range(len(fields)):
                marked = False
                if nonzero and all(item[i] == '0' or item[i] == 'NO DATA' for item in records):
                    del_columns.append(i)
                    marked = True
                if unique and not marked:
                    column_vals = [item[i] for item in records]
                    if len(set(column_vals)) == 1:
                        del_columns.append(i)
            del_columns.reverse()
            for val in del_columns:
                for row in records:
                    del row[val]
                del fields[val]
            if len(fields) > 0:
                matrix = records
        if not nonzero and not unique:
            for endpoint in endpoints:
                record = []
                for field in fields:
                    record.append(fields_lookup[field.lower()][0](endpoint))
                matrix.append(record)
        if len(matrix) > 0:
            matrix = sorted(matrix, key=lambda endpoint: endpoint[sort_by])
            # swap out field names for header
            fields_header = []
            for field in fields:
                fields_header.append(
                    self.all_fields[fields_lookup[field.lower()][1]])
            # set the header
            matrix.insert(0, fields_header)
            table = Texttable(max_width=max_width)
            # make all the column types be text
            table.set_cols_dtype(['t']*len(fields))
            table.add_rows(matrix)
            print(table.draw())
        else:
            print('No results found for that query.')
        return


class PoseidonShell(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(
            self, persistent_history_file='/root/.poseidon_history')
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
        self.file = None

        self.show_completions = [
            'role active-directory-controller', 'role administrator-server',
            'role administrator-workstation', 'role business-workstation',
            'role developer-workstation', 'role gpu-laptop', 'role pki-server',
            'role unknown', 'state active', 'state inactive', 'state known',
            'state unknown', 'state mirroring', 'state abnormal', 'state shutdown',
            'state reinvestigating', 'state queued', 'state ignored',
            'behavior normal', 'behavior abnormal', 'os windows', 'os freebsd',
            'os linux', 'os mac', 'history', 'what', 'where', 'all'
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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

    @exception
    def show_role(self, arg, flags):
        '''Show all things on the network that match a role'''
        fields = self.parser.default_fields

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

    @exception
    def show_state(self, arg, flags):
        '''Show all things on the network that match a state'''
        fields = ['Switch', 'Port', 'State',
                  'Ethernet Vendor', 'Mac', 'IPv4', 'IPv6']

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

    @exception
    def show_behavior(self, arg, flags):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields + ['Behavior']

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

    @exception
    def show_os(self, arg, flags):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().what_is(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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
        fields = ['Previous States']

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(
            Commands().history_of(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(
            Commands().where_is(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

    @exception
    def help_show(self):
        self.poutput('  all\t\tShow all devices')
        self.poutput('  behavior\tShow devices matching a particular behavior')
        self.poutput(
            '  history\tFind out the history of something on the network')
        self.poutput(
            '  os\t\tShow devices matching a particular operating system')
        self.poutput('  role\t\tShow devices matching a particular role')
        self.poutput('  state\t\tShow devices matching a particular state')
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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.poutput('Set the following device states:')
        self.parser.display_results(Commands().change_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.poutput('Ignored the following devices:')
        self.parser.display_results(
            Commands().ignore(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        self.poutput('Cleared the following devices that were being ignored:')
        self.parser.display_results(
            Commands().clear_ignored(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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

        fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = self.parser._check_flags(
            flags, fields)

        endpoints = []
        if arg.startswith('ignored'):
            endpoints = Commands().remove_ignored(arg)
        elif arg.startswith('inactive'):
            endpoints = Commands().remove_inactives(arg)
        else:
            endpoints = Commands().remove(arg)
        self.poutput('Removed the following devices:')
        self.parser.display_results(
            endpoints, fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero, output_format=output_format, ipv4_only=ipv4_only, ipv6_only=ipv6_only, ipv4_and_ipv6=ipv4_and_ipv6)

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
        flags, arg = self.parser.get_flags(arg)
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
        flags, arg = self.parser.get_flags(arg)
        if arg:
            action = arg.split()[0]
            func_calls = {'all': self.show_all,
                          'authors': self.show_authors,
                          'behavior': self.show_behavior,
                          'history': self.show_history,
                          'os': self.show_os,
                          'role': self.show_role,
                          'state': self.show_state,
                          'what': self.show_what,
                          'where': self.show_where}
            if action in func_calls:
                if action in ['all', 'authors']:
                    func_calls[action](arg, flags)
                elif action in ['history', 'what', 'where']:
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
    def do_eof(self, arg):
        self.close()
        return True

    @exception
    def do_quit(self, arg):
        '''Stop the shell and exit:  QUIT'''
        self.poutput('Thank you for using Poseidon')
        self.close()
        return True

    @exception
    def do_exit(self, arg):
        '''Stop the shell and exit:  EXIT'''
        self.poutput('Thank you for using Poseidon')
        self.close()
        return True

    @exception
    def do_help(self, arg):
        if not arg:
            self.poutput('For help on specific commands: help <command>')
            self.poutput('Commands:')
            self.poutput('  exit\t\t\tStop the shell and exit')
            self.poutput(
                '  fields\t\tList out all available field names - TO BE IMPLEMENTED')
            self.poutput('  playback\t\tPlayback commands from a file')
            self.poutput('  quit\t\t\tStop the shell and exit')
            self.poutput('  record\t\tSave future commands to a file')
            self.poutput(
                '  shell\t\t\tExecutes commands on the shell inside the Poseidon container')
            self.poutput(
                '  show\t\t\tShow things on the network based on filters')
            self.poutput(
                '  set\t\t\tApply settings for all future commands in this session - TO BE IMPLEMENTED')
            self.poutput('  task\t\t\tPerform a task on things on the network')
            self.poutput()
            self.poutput('Optional flags that can be combined with commands:')
            self.poutput(
                '  --fields\t\tSpecify which fields to display, i.e. --fields=[id, mac]')
            self.poutput(
                '  --max_width\t\tSpecify a max width of characters for output, i.e. --max_width=80')
            self.poutput('  --output_format\tTO BE IMPLEMENTED')
            self.poutput(
                '  --sort_by\t\tSort the output by a specific column index, i.e. --sort_by=0')
            self.poutput()
            self.poutput('Boolean flags that can be combined with commands:')
            self.poutput('  -4and6\t\tShow fields for both IPv4 and IPv6')
            self.poutput('  -4\t\t\tShow only IPv4 fields')
            self.poutput('  -6\t\t\tShow only IPv6 fields')
            self.poutput(
                '  -nonzero\t\tRemoves rows and columns that contain only "0"s or "NO DATA"')
            self.poutput(
                '  -unique\t\tRemoves columns that all contain the same value')
        else:
            cmd.Cmd.do_help(self, arg)

    def emptyline(self):
        pass

    @exception
    def do_shell(self, s):
        '''Execute shell commands inside the Poseidon container'''
        os.system(s)

    @exception
    def do_record(self, arg):
        '''Save future commands to filename: RECORD poseidon.cmd'''
        if arg:
            self.file = open(arg, 'w')
        else:
            self.poutput('PLAYBACK <FILENAME>')

    @exception
    def do_playback(self, arg):
        '''Playback commands from a file: PLAYBACK poseidon.cmd'''
        if arg:
            self.close()
            with open(arg) as f:
                self.cmdqueue.extend(f.read().splitlines())
        else:
            self.poutput('PLAYBACK <FILENAME>')

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        if '?' in line:
            line = line.replace('?', '')
            line = '? ' + line
        return line

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        names = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        if 'eof' in names:
            names.remove('eof')
        if 'shell' in names:
            names.remove('shell')
        return names

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


if __name__ == '__main__':  # pragma: no cover
    p_shell = PoseidonShell()
    p_shell.cmdloop()
