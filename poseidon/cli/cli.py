#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for the Poseidon shell.

Created on 14 January 2019
@author: Charlie Lewis
"""
import cmd
import os
import time

from natural.date import delta
from natural.date import duration
from texttable import Texttable

from poseidon.cli.commands import Commands
from poseidon.helpers.exception_decor import exception


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
    def _get_ignored(endpoint):
        return str(endpoint.ignore)

    @staticmethod
    def _get_state(endpoint):
        return endpoint.state

    @staticmethod
    def _get_next_state(endpoint):
        return endpoint.p_next_state

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
            'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4', 'IPv6',
            'Ethernet Vendor', 'Ignored', 'State', 'Next State', 'First Seen',
            'Last Seen', 'Previous States', 'IPv4 OS', 'IPv6 OS',
            'Previous IPv4 OSes', 'Previous IPv6 OSes', 'Role',
            'Role Confidence', 'Previous Roles', 'Previous Role Confidences',
            'Behavior', 'Previous Behaviors', 'IPv4 rDNS', 'IPv6 rDNS'
        ]

    def completion(self, text, line, completions):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in completions if s.lower().startswith(mline.lower())]

    def get_flags(self, text):
        flags = {}
        not_flags = []
        # remove boolean flags first
        words = text.split()
        other_words = []
        for word in words:
            if len(word) > 2 and word[0] == '-' and word[1] != '-':
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

    def _check_flags(self, flags, fields, sort_by=0, max_width=0, unique=False, nonzero=False):
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
        return fields, sort_by, max_width, unique, nonzero

    def display_results(self, endpoints, fields, sort_by=0, max_width=0, unique=False, nonzero=False):
        matrix = []
        fields_lookup = {'id': (GetData._get_name, 0),
                         'mac': (GetData._get_mac, 1),
                         'mac address': (GetData._get_mac, 1),
                         'switch': (GetData._get_switch, 2),
                         'port': (GetData._get_port, 3),
                         'vlan': (GetData._get_vlan, 4),
                         'ipv4': (GetData._get_ipv4, 5),
                         'ipv6': (GetData._get_ipv6, 6),
                         'ethernet vendor': (GetData._get_ether_vendor, 7),
                         'ignored': (GetData._get_ignored, 8),
                         'state': (GetData._get_state, 9),
                         'next state': (GetData._get_next_state, 10),
                         'first seen': (GetData._get_first_seen, 11),
                         'last seen': (GetData._get_last_seen, 12),
                         'previous states': (GetData._get_prev_states, 13),
                         'ipv4 os': (GetData._get_ipv4_os, 14),
                         'ipv6 os': (GetData._get_ipv6_os, 15),
                         'previous ipv4 oses': (GetData._get_prev_ipv4_oses, 16),
                         'previous ipv6 oses': (GetData._get_prev_ipv6_oses, 17),
                         'role': (GetData._get_role, 18),
                         'role confidence': (GetData._get_role_confidence, 19),
                         'previous roles': (GetData._get_prev_roles, 20),
                         'previous role confidences': (GetData._get_prev_role_confidences, 21),
                         'behavior': (GetData._get_behavior, 22),
                         'previous behaviors': (GetData._get_prev_behaviors, 23),
                         'ipv4 rdns': (GetData._get_ipv4_rdns, 24),
                         'ipv6 rdns': (GetData._get_ipv6_rdns, 25)}
        # TODO #971 check if unique flag and limit columns (fields)
        # TODO #963 check if nonzero flag and limit rows/columns
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


class ShowInterpreter(cmd.Cmd):

    def __init__(self, file=None, prompt='', cmdqueue=[]):
        cmd.Cmd.__init__(self)
        self.file = file
        self.prompt = prompt + '(show) '
        self.cmdqueue = cmdqueue
        self.parser = Parser()
        self.role_completions = [
            'active-directory-controller', 'administrator-server',
            'administrator-workstation', 'business-workstation',
            'developer-workstation', 'gpu-laptop', 'pki-server', 'unknown'
        ]
        self.state_completions = [
            'active', 'inactive', 'known', 'unknown', 'mirroring', 'abnormal',
            'shutdown', 'reinvestigating', 'queued', 'ignored'
        ]
        self.behavior_completions = [
            'normal', 'abnormal'
        ]
        self.os_completions = [
            'windows', 'freebsd', 'linux', 'mac'
        ]

    def complete_role(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.role_completions)

    def complete_behavior(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.behavior_completions)

    def complete_os(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.os_completions)

    def complete_state(self, text, line, begidx, endidx):
        return self.parser.completion(text, line, self.state_completions)

    @exception
    def do_all(self, arg):
        '''Show all things on the network'''
        fields = self.parser.default_fields

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg, 'all'), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_role(self, arg):
        '''Show all things on the network that match a role'''
        fields = self.parser.default_fields

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg, 'role'), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_state(self, arg):
        '''Show all things on the network that match a state'''
        fields = ['Switch', 'Port', 'State',
                  'Ethernet Vendor', 'Mac', 'IPv4', 'IPv6']

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg, 'state'), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_behavior(self, arg):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields + ['Behavior']

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg, 'behavior'), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_os(self, arg):
        '''Show all things on the network that match a behavior'''
        fields = self.parser.default_fields

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().show_devices(
            arg, 'os'), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_what(self, arg):
        '''
        Find out what something is:
        WHAT [IP|MAC|ID]
        WHAT 10.0.0.1
        WHAT 18:EF:02:2D:49:00
        WHAT 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = self.parser.all_fields

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(Commands().what_is(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_history(self, arg):
        '''
        Find out the history of something on the network:
        HISTORY [IP|MAC|ID]
        HISTORY 10.0.0.1
        HISTORY 18:EF:02:2D:49:00
        HISTORY 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['Previous States']

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(
            Commands().history_of(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_where(self, arg):
        '''
        Find out where something is:
        WHERE [IP|MAC|ID]
        WHERE 10.0.0.1
        WHERE 18:EF:02:2D:49:00
        WHERE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['Switch', 'Port', 'VLAN', 'IPv4', 'IPv6', 'MAC Address']

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        self.parser.display_results(
            Commands().where_is(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_help(self, arg):
        if not arg:
            print('For help on specific commands: help <command>')
            print('Commands:')
            print('  all\t\tShow all devices')
            print('  behavior\tShow devices matching a particular behavior')
            print('  exit\t\tGo back to the main prompt')
            print('  history\tFind out the history of something on the network')
            print('  os\t\tShow devices matching a particular operating system')
            print('  quit\t\tGo back to the main prompt')
            print('  role\t\tShow devices matching a particular role')
            print('  state\t\tShow devices matching a particular state')
            print('  what\tFind out what something is')
            print('  where\tFind out where something is')
        else:
            cmd.Cmd.do_help(self, arg)

    @exception
    def do_authors(self, arg):
        print("""\033[1;34m                            The Cyber Reboot Team
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
        with open('/poseidon/AUTHORS', 'r') as f:
            i = 1
            for line in f:
                if i > 4:
                    print(line.strip())
                i += 1

    def emptyline(self):
        pass

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        names = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        if 'eof' in names:
            names.remove('eof')
        if 'authors' in names:
            names.remove('authors')
        if 'shell' in names:
            names.remove('shell')
        return names

    @exception
    def do_shell(self, s):
        '''Execute shell commands inside the Poseidon container'''
        os.system(s)

    @exception
    def do_exit(self, arg):
        '''Go back to the main prompt:  EXIT'''
        return True

    @exception
    def do_quit(self, arg):
        '''Go back to the main prompt:  QUIT'''
        return True

    @exception
    def do_eof(self, arg):
        return True

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        if '?' in line:
            line = line.replace('?', '')
            line = '? ' + line
        return line


class TaskInterpreter(cmd.Cmd):

    def __init__(self, file=None, prompt='', cmdqueue=[]):
        cmd.Cmd.__init__(self)
        self.file = file
        self.prompt = prompt + '(task) '
        self.cmdqueue = cmdqueue
        self.parser = Parser()

    @exception
    def do_set(self, arg):
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

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        print('Set the following device states:')
        self.parser.display_results(Commands().change_devices(
            arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_collect(self, arg):
        '''
        Collect on something on the network for a duration:
        COLLECT [IP|MAC|ID] [DURATION] (TODO - NOT IMPLEMENTED YET)
        '''
        # TODO
        print('Not implemented yet')

    @exception
    def do_ignore(self, arg):
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

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        print('Ignored the following devices:')
        self.parser.display_results(
            Commands().ignore(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_clear(self, arg):
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

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        print('Cleared the following devices that were being ignored:')
        self.parser.display_results(
            Commands().clear_ignored(arg), fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    @exception
    def do_remove(self, arg):
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

        flags, arg = self.parser.get_flags(arg)
        fields, sort_by, max_width, unique, nonzero = self.parser._check_flags(
            flags, fields)

        endpoints = []
        if arg.startswith('ignored'):
            endpoints = Commands().remove_ignored(arg)
        elif arg.startswith('inactive'):
            endpoints = Commands().remove_inactives(arg)
        else:
            endpoints = Commands().remove(arg)
        print('Removed the following devices:')
        self.parser.display_results(
            endpoints, fields, sort_by=sort_by, max_width=max_width, unique=unique, nonzero=nonzero)

    def emptyline(self):
        pass

    @exception
    def do_shell(self, s):
        '''Execute shell commands inside the Poseidon container'''
        os.system(s)

    @exception
    def do_help(self, arg):
        if not arg:
            print('For help on specific commands: help <command>')
            print('Commands:')
            print('  clear\t\tStop ignoring something on the network')
            print('  collect\tCollect on something on the network for a duration')
            print('  exit\t\tGo back to the main prompt')
            print('  ignore\tIgnore something on the network')
            print('  quit\t\tGo back to the main prompt')
            print(
                '  remove\tRemove something on the network until it is seen again')
            print('  set\t\tSet the state of things on the network')
        else:
            cmd.Cmd.do_help(self, arg)

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        names = [a[3:] for a in self.get_names() if a.startswith(dotext)]
        if 'eof' in names:
            names.remove('eof')
        if 'shell' in names:
            names.remove('shell')
        return names

    @exception
    def do_exit(self, arg):
        '''Go back to the main prompt:  EXIT'''
        return True

    @exception
    def do_quit(self, arg):
        '''Go back to the main prompt:  QUIT'''
        return True

    @exception
    def do_eof(self, arg):
        return True

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        if '?' in line:
            line = line.replace('?', '')
            line = '? ' + line
        return line


class PoseidonShell(cmd.Cmd):
    intro = """Welcome to the Poseidon shell. Type help or ? to list commands.
                               _      \033[1;31m__\033[1;m
    ____   ____   \033[1;31m_____\033[1;m ___   (_)\033[1;31m____/ /\033[1;m____   \033[1;31m____\033[1;m
   / __ \ / __ \ \033[1;31m/ ___/\033[1;m/ _ \ / /\033[1;31m/ __  /\033[1;m/ __ \ \033[1;31m/ __ \\\033[1;m
  / /_/ // /_/ /\033[1;31m(__  )\033[1;m/  __// /\033[1;31m/ /_/ /\033[1;m/ /_/ /\033[1;31m/ / / /\033[1;m
 / .___/ \____/\033[1;31m/____/\033[1;m \___//_/ \033[1;31m\__,_/\033[1;m \____/\033[1;31m/_/ /_/\033[1;m
/_/"""
    prompt = '\033[1;32mposeidon$ \033[1;m'
    file = None

    @exception
    def do_task(self, arg):
        '''Perform task to things on the network'''
        if not self.cmdqueue:
            self.cmdqueue.append(arg)
        sub_cmd = TaskInterpreter(
            file=self.file, prompt=self.prompt, cmdqueue=self.cmdqueue)
        sub_cmd.cmdloop()

    @exception
    def do_show(self, arg):
        '''Show things on the network based on filters'''
        if not self.cmdqueue:
            self.cmdqueue.append(arg)
        sub_cmd = ShowInterpreter(
            file=self.file, prompt=self.prompt, cmdqueue=self.cmdqueue)
        sub_cmd.cmdloop()

    @exception
    def do_eof(self, arg):
        self.close()
        return True

    @exception
    def do_quit(self, arg):
        '''Stop the shell and exit:  QUIT'''
        print('Thank you for using Poseidon')
        self.close()
        return True

    @exception
    def do_exit(self, arg):
        '''Stop the shell and exit:  EXIT'''
        print('Thank you for using Poseidon')
        self.close()
        return True

    @exception
    def do_help(self, arg):
        if not arg:
            print('For help on specific commands: help <command>')
            print('Commands:')
            print('  exit\t\tStop the shell and exit')
            print('  playback\tPlayback commands from a file')
            print('  quit\t\tStop the shell and exit')
            print('  record\tSave future commands to a file')
            print('  show\t\tShow things on the network based on filters')
            print('  task\t\tPerform a task on things on the network')
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
        self.file = open(arg, 'w')

    @exception
    def do_playback(self, arg):
        '''Playback commands from a file: PLAYBACK poseidon.cmd'''
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

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
    PoseidonShell().cmdloop()
