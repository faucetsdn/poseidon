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
    def display_results(endpoints, fields, sort_by):
        matrix = []
        fields_lookup = {'ID': PoseidonShell._get_name,
                         'MAC Address': PoseidonShell._get_mac,
                         'Switch': PoseidonShell._get_switch,
                         'Port': PoseidonShell._get_port,
                         'VLAN': PoseidonShell._get_vlan,
                         'IPv4': PoseidonShell._get_ipv4,
                         'IPv6': PoseidonShell._get_ipv6,
                         'Ignored': PoseidonShell._get_ignored,
                         'State': PoseidonShell._get_state,
                         'Next State': PoseidonShell._get_next_state,
                         'Previous States': PoseidonShell._get_prev_states}
        for endpoint in endpoints:
            record = []
            for field in fields:
                record.append(fields_lookup[field](endpoint))
            matrix.append(record)
        if len(matrix) > 0:
            matrix = sorted(matrix, key=lambda endpoint: endpoint[sort_by])
            # set the header
            matrix.insert(0, fields)
            table = Texttable(max_width=100)
            # make all the column types be text
            table.set_cols_dtype(['t']*len(fields))
            table.add_rows(matrix)
            print(table.draw())
        else:
            print('No results found for that query.')
        return

    def complete_what(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.what_completions)

    def complete_show(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.show_completions)

    def complete_clear(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.clear_completions)

    def complete_ignore(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.ignore_completions)

    def complete_remove(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.remove_completions)

    def do_what(self, arg):
        '''
        Find out what something is:
        WHAT IS [IP|MAC|ID]
        WHAT IS 10.0.0.1
        WHAT IS 18:EF:02:2D:49:00
        WHAT IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # TODO print more info
        PoseidonShell.display_results(Commands().what_is(
            arg), self.default_fields + ['State', 'Next State', 'Previous States'], 0)

    def do_where(self, arg):
        '''
        Find out where something is:
        WHERE IS [IP|MAC|ID]
        WHERE IS 10.0.0.1
        WHERE IS 18:EF:02:2D:49:00
        WHERE IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # TODO print where info specifically
        PoseidonShell.display_results(
            Commands().where_is(arg), ['ID', 'MAC Address', 'Switch', 'Port'], 0)

    def do_collect(self, arg):
        '''
        TODO - NOT IMPLEMENTED YET

        Collect on something on the network:
        COLLECT ON [IP|MAC]
        COLLECT ON 10.0.0.1 FOR 300 SECONDS
        COLLECT ON 18:EF:02:2D:49:00 FOR 5 MINUTES
        '''
        print('Collecting on the following devices:')
        PoseidonShell.display_results(
            Commands().collect_on(arg), self.default_fields, 0)

    def do_ignore(self, arg):
        '''
        Ignore something on the network:
        IGNORE [IP|MAC|ID]
        IGNORE 10.0.0.1
        IGNORE 18:EF:02:2D:49:00
        IGNORE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        IGNORE INACTIVE DEVICES
        '''
        print('Ignored the following devices:')
        PoseidonShell.display_results(
            Commands().ignore(arg), self.default_fields, 0)

    def do_clear(self, arg):
        '''
        Stop ignoring something on the network:
        CLEAR [IP|MAC|ID]
        CLEAR 10.0.0.1
        CLEAR 18:EF:02:2D:49:00
        CLEAR 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        CLEAR IGNORED DEVICES
        '''
        print('Cleared the following devices that were being ignored:')
        PoseidonShell.display_results(
            Commands().clear_ignored(arg), self.default_fields, 0)

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
        endpoints = []
        if arg.startswith('ignored'):
            endpoints = Commands().remove_ignored(arg)
        elif arg.startswith('inactive'):
            endpoints = Commands().remove_inactives(arg)
        else:
            endpoints = Commands().remove(arg)
        print('Removed the following devices:')
        PoseidonShell.display_results(endpoints, self.default_fields, 0)

    def do_show(self, arg):
        '''
        Show things on the network based on filters:
        SHOW ACTIVE DEVICES
        SHOW INACTIVE DEVICES
        SHOW WINDOWS DEVICES
        SHOW ABNORMAL DEVICES
        '''
        PoseidonShell.display_results(Commands().show_devices(
            arg), self.default_fields + ['State', 'Next State'], 0)

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
