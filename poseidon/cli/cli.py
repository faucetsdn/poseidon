#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for the Poseidon shell.

Created on 14 January 2019
@author: Charlie Lewis
"""
import cmd

from texttable import Texttable

from poseidon.cli.commands import Commands


class PoseidonShell(cmd.Cmd):
    intro = 'Welcome to the Poseidon shell. Type help or ? to list commands.\n'
    prompt = '\033[1;32mposeidon$ \033[1;m'
    file = None

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
    def display_results(endpoints, fields, sortby):
        matrix = []
        for endpoint in endpoints:
            vlan = endpoint.endpoint_data['tenant']
            if vlan.startswith('VLAN'):
                vlan = vlan.split('VLAN')[1]
            # TODO add options to modify the columns
            matrix.append([endpoint.machine.name.strip(),
                           endpoint.endpoint_data['mac'],
                           endpoint.endpoint_data['segment'],
                           endpoint.endpoint_data['port'],
                           vlan, endpoint.endpoint_data['ipv4'],
                           endpoint.endpoint_data['ipv6']])
        if len(matrix) > 0:
            # TODO add options to maodify the sorted by key and the header options
            matrix = sorted(matrix, key=lambda endpoint: endpoint[1])
            matrix.insert(0, ['Name', 'MAC Address', 'Segment',
                              'Port', 'VLAN', 'IPv4', 'IPv6'])
            table = Texttable(max_width=0)
            # make all the columns types be text
            table.set_cols_dtype(['t']*7)
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

    @staticmethod
    def do_what(arg):
        '''
        Find out what something is:
        WHAT IS 10.0.0.1
        WHAT IS 18:EF:02:2D:49:00
        WHAT IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # TODO
        Commands().what_is(arg)

    @staticmethod
    def do_where(arg):
        '''
        Find out where something is:
        WHERE IS 10.0.0.1
        WHERE IS 18:EF:02:2D:49:00
        WHERE IS 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        '''
        # TODO
        Commands().where_is(arg)

    @staticmethod
    def do_collect(arg):
        '''
        Collect on something on the network:
        COLLECT ON 10.0.0.1 FOR 300 SECONDS
        COLLECT ON 18:EF:02:2D:49:00 FOR 5 MINUTES
        '''
        # TODO
        Commands().collect_on(arg)

    @staticmethod
    def do_ignore(arg):
        '''
        Ignore something on the network:
        IGNORE 10.0.0.1
        IGNORE 18:EF:02:2D:49:00
        IGNORE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        IGNORE INACTIVE DEVICES
        '''
        print('Ignored the following devices:')
        PoseidonShell.display_results(Commands().ignore(arg), None, None)

    @staticmethod
    def do_clear(arg):
        '''
        Stop ignoring something on the network:
        CLEAR 10.0.0.1
        CLEAR 18:EF:02:2D:49:00
        CLEAR 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293
        CLEAR IGNORED DEVICES
        '''
        print('Cleared the following devices that were being ignored:')
        PoseidonShell.display_results(
            Commands().clear_ignored(arg), None, None)

    @staticmethod
    def do_remove(arg):
        '''
        Remove and forget about something on the network until it's seen again:
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
        PoseidonShell.display_results(endpoints, None, None)

    def do_show(self, arg):
        '''
        Show things on the network based on filters:
        SHOW ACTIVE DEVICES
        SHOW INACTIVE DEVICES
        SHOW WINDOWS DEVICES
        SHOW ABNORMAL DEVICES
        '''
        endpoints = Commands().show_devices(arg)
        matrix = []
        for endpoint in endpoints:
            vlan = endpoint.endpoint_data['tenant']
            if vlan.startswith('VLAN'):
                vlan = vlan.split('VLAN')[1]
            # TODO add options to modify the columns
            matrix.append([endpoint.machine.name.strip(), endpoint.state,
                           endpoint.endpoint_data['mac'],
                           endpoint.endpoint_data['segment'],
                           endpoint.endpoint_data['port'],
                           vlan, endpoint.endpoint_data['ipv4'],
                           endpoint.endpoint_data['ipv6'],
                           endpoint.p_next_state])
        if len(matrix) > 0:
            # TODO add options to maodify the sorted by key and the header options
            matrix = sorted(matrix, key=lambda endpoint: endpoint[2])
            matrix.insert(0, ['Name', 'State', 'MAC Address', 'Segment',
                              'Port', 'VLAN', 'IPv4', 'IPv6', 'Next State'])
            table = Texttable(max_width=0)
            # make all the columns types be text
            table.set_cols_dtype(['t']*9)
            table.add_rows(matrix)
            print(table.draw())
        elif not arg in self.show_completions:
            print('Invalid query, try using TAB to see available options')
        else:
            print('No results found for that query.')

    @staticmethod
    def do_change(arg):
        '''
        Change state of things on the network:
        CHANGE 10.0.0.1 TO INACTIVE
        CHANGE ABNORMAL DEVICES TO UNKNOWN
        CHANGE 18:EF:02:2D:49:00 TO KNOWN
        CHANGE 8579d412f787432c1a3864c1833e48efb6e61dd466e39038a674f64652129293 TO SHUTDOWN
        '''
        # TODO
        Commands().where_is(arg)

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
