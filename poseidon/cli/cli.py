#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for the Poseidon shell.

Created on 14 January 2019
@author: Charlie Lewis
"""
import cmd
import time

from natural.date import delta
from natural.date import duration
from texttable import Texttable

from poseidon.cli.commands import Commands


class PoseidonShell(cmd.Cmd):
    intro = 'Welcome to the Poseidon shell. Type help or ? to list commands.\n'
    prompt = '\033[1;32mposeidon$ \033[1;m'
    file = None

    default_fields = ['ID', 'MAC Address',
                      'Switch', 'Port', 'VLAN', 'IPv4', 'IPv6']
    what_completions = [
        'is'
    ]
    where_completions = [
        'is'
    ]
    collect_completions = [
        'on'
    ]
    history_completions = [
        'of'
    ]
    clear_completions = [
        'ignored devices'
    ]
    ignore_completions = [
        'inactive devices'
    ]
    remove_completions = [
        'ignored devices',
        'inactive devices'
    ]
    show_completions = [
        'all devices', 'active devices', 'inactive devices', 'known devices',
        'unknown devices', 'mirroring devices', 'abnormal devices',
        'shutdown devices', 'reinvestigating devices', 'queued devices',
        'active directory controller devices', 'administrator server devices',
        'administrator workstation devices', 'business workstation devices',
        'developer workstation devices', 'gpu laptop devices',
        'pki server devices', 'windows devices', 'mac devices',
        'linux devices', 'ignored devices'
    ]

    @staticmethod
    def get_flags(text):
        flags = {}
        not_flags = []
        first = text.split('--')
        not_flags += first[0].split()
        first.pop(0)
        for flag in first:
            if '=' in flag:
                command, value = flag.split('=', 1)
                if '[' in value and ']' in value:
                    val = value.rsplit(']', 1)[0].split('[', 1)[1]
                    flags[command] = [val]
                    not_f = value.rsplit(']', 1)
                else:
                    val = value.split(' ', 1)[0]
                    flags[command] = val
                    not_f = value.split(' ', 1)
                not_f.pop(0)
                if not_f:
                    not_flags += not_f[0].split()
        return flags, ' '.join(not_flags)

    @staticmethod
    def completion(text, line, completions):
        # TODO handle expectation of '?'
        if line.endswith('?'):
            pass

        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in completions if s.lower().startswith(mline.lower())]

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
        return endpoint.endpoint_data['ipv4']

    @staticmethod
    def _get_ipv6(endpoint):
        return endpoint.endpoint_data['ipv6']

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
        # TODO
        return

    @staticmethod
    def _get_last_seen(endpoint):
        # TODO
        return

    @staticmethod
    def _get_prev_states(endpoint):
        prev_states = endpoint.p_prev_states
        oldest_state = []
        output = 'None'
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
    def display_results(endpoints, fields, sort_by=0, max_width=0):
        matrix = []
        fields_lookup = {'id': PoseidonShell._get_name,
                         'mac address': PoseidonShell._get_mac,
                         'switch': PoseidonShell._get_switch,
                         'port': PoseidonShell._get_port,
                         'vlan': PoseidonShell._get_vlan,
                         'ipv4': PoseidonShell._get_ipv4,
                         'ipv6': PoseidonShell._get_ipv6,
                         'ignored': PoseidonShell._get_ignored,
                         'state': PoseidonShell._get_state,
                         'next state': PoseidonShell._get_next_state,
                         'first seen': PoseidonShell._get_first_seen,
                         'last seen': PoseidonShell._get_last_seen,
                         'previous states': PoseidonShell._get_prev_states}
        for endpoint in endpoints:
            record = []
            for field in fields:
                record.append(fields_lookup[field.lower()](endpoint))
            matrix.append(record)
        if len(matrix) > 0:
            matrix = sorted(matrix, key=lambda endpoint: endpoint[sort_by])
            # set the header
            matrix.insert(0, fields)
            table = Texttable(max_width=max_width)
            # make all the column types be text
            table.set_cols_dtype(['t']*len(fields))
            table.add_rows(matrix)
            print(table.draw())
        else:
            print('No results found for that query.')
        return

    def complete_what(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.what_completions)

    def complete_history(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.history_completions)

    def complete_show(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.show_completions)

    def complete_clear(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.clear_completions)

    def complete_ignore(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.ignore_completions)

    def complete_remove(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.remove_completions)

    @staticmethod
    def _check_flags(flags, fields, sort_by=0, max_width=0):
        for flag in flags:
            if flag == 'fields':
                fields = flags[flag]
            elif flag == 'sort_by':
                sort_by = int(flags[flag])
            elif flag == 'max_width':
                max_width = int(flags[flag])
        return fields, sort_by, max_width

    def do_what(self, arg):
        '''
        Find out what something is:
        WHAT IS [IP|MAC|ID]
        WHAT IS 10.0.0.1
        WHAT IS 18:EF:02:2D:49:00
        WHAT IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = self.default_fields + \
            ['State', 'Next State', 'First Seen', 'Last Seen']

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        # TODO print more info
        PoseidonShell.display_results(Commands().what_is(
            arg), fields, sort_by=sort_by, max_width=max_width)

    def do_history(self, arg):
        '''
        Find out the history of something on the network:
        HISTORY OF [IP|MAC|ID]
        HISTORY OF 10.0.0.1
        HISTORY OF 18:EF:02:2D:49:00
        HISTORY OF 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = self.default_fields + \
            ['State', 'Next State', 'Previous States']

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        PoseidonShell.display_results(
            Commands().history_of(arg), fields, sort_by=sort_by, max_width=max_width)

    def do_where(self, arg):
        '''
        Find out where something is:
        WHERE IS [IP|MAC|ID]
        WHERE IS 10.0.0.1
        WHERE IS 18:EF:02:2D:49:00
        WHERE IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # defaults
        fields = ['ID', 'MAC Address', 'Switch', 'Port']

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        PoseidonShell.display_results(
            Commands().where_is(arg), fields, sort_by=sort_by, max_width=max_width)

    def do_collect(self, arg):
        '''
        TODO - NOT IMPLEMENTED YET

        Collect on something on the network:
        COLLECT ON [IP|MAC]
        COLLECT ON 10.0.0.1 FOR 300 SECONDS
        COLLECT ON 18:EF:02:2D:49:00 FOR 5 MINUTES
        '''
        # defaults
        fields = self.default_fields

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        print('Collecting on the following devices:')
        PoseidonShell.display_results(
            Commands().collect_on(arg), fields, sort_by=sort_by, max_width=max_width)

    def do_ignore(self, arg):
        '''
        Ignore something on the network:
        IGNORE [IP|MAC|ID]
        IGNORE 10.0.0.1
        IGNORE 18:EF:02:2D:49:00
        IGNORE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        IGNORE INACTIVE DEVICES
        '''
        # defaults
        fields = self.default_fields

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        print('Ignored the following devices:')
        PoseidonShell.display_results(
            Commands().ignore(arg), fields, sort_by=sort_by, max_width=max_width)

    def do_clear(self, arg):
        '''
        Stop ignoring something on the network:
        CLEAR [IP|MAC|ID]
        CLEAR 10.0.0.1
        CLEAR 18:EF:02:2D:49:00
        CLEAR 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        CLEAR IGNORED DEVICES
        '''
        # defaults
        fields = self.default_fields

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        print('Cleared the following devices that were being ignored:')
        PoseidonShell.display_results(
            Commands().clear_ignored(arg), fields, sort_by=sort_by, max_width=max_width)

    def do_remove(self, arg):
        '''
        Remove and forget about something on the network until it's seen again:
        REMOVE [IP|MAC|ID]
        REMOVE 10.0.0.1
        REMOVE 18:EF:02:2D:49:00
        REMOVE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        REMOVE IGNORED DEVICES
        REMOVE INACTIVE DEVICES
        '''
        # defaults
        fields = self.default_fields

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        endpoints = []
        if arg.startswith('ignored'):
            endpoints = Commands().remove_ignored(arg)
        elif arg.startswith('inactive'):
            endpoints = Commands().remove_inactives(arg)
        else:
            endpoints = Commands().remove(arg)
        print('Removed the following devices:')
        PoseidonShell.display_results(
            endpoints, fields, sort_by=sort_by, max_width=max_width)

    def do_show(self, arg):
        '''
        Show things on the network based on filters:
        SHOW ACTIVE DEVICES
        SHOW INACTIVE DEVICES
        SHOW WINDOWS DEVICES
        SHOW ABNORMAL DEVICES
        '''
        # defaults
        fields = self.default_fields + ['State', 'Next State']

        flags, arg = PoseidonShell.get_flags(arg)
        fields, sort_by, max_width = PoseidonShell._check_flags(flags, fields)

        PoseidonShell.display_results(Commands().show_devices(
            arg), fields, sort_by=sort_by, max_width=max_width)

    @staticmethod
    def do_change(arg):
        '''
        TODO - NOT IMPLEMENTED YET

        Change state of things on the network:
        CHANGE [IP|MAC|ID] TO [STATE]
        CHANGE 10.0.0.1 TO INACTIVE
        CHANGE ABNORMAL DEVICES TO UNKNOWN
        CHANGE 18:EF:02:2D:49:00 TO KNOWN
        CHANGE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293 TO SHUTDOWN
        '''
        # TODO
        return

    def do_quit(self, arg):
        'Stop recording and exit:  QUIT'
        print('Thank you for using Poseidon')
        self.close()
        return True

    def do_record(self, arg):
        'Save future commands to filename: RECORD poseidon.cmd'
        self.file = open(arg, 'w')

    def do_playback(self, arg):
        'Playback commands from a file: PLAYBACK poseidon.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


if __name__ == '__main__':  # pragma: no cover
    PoseidonShell().cmdloop()
