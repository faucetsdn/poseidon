import cmd

from poseidon.main import SDNConnect


class Commands:

    def what_is(self, args):
        ''' what is a specific thing '''
        return

    def where_is(self, args):
        ''' where topologically is a specific thing '''
        return

    def collect_on(self, args):
        ''' collect on a specific thing '''
        return

    def clear_inactives(self, args):
        ''' clear out all inactive devices '''
        return

    def ignore(self, args):
        ''' ignore a specific thing '''
        return

    def show_ignored(self, args):
        ''' show all things that are being ignored '''
        return

    def remove_ignored(self, args):
        ''' stop ignoriing a specific thing '''
        return

    def remove(self, args):
        ''' remove and forget about a specific thing until it's seen again '''
        return

    def show_state(self, args):
        ''' show all devices that are in a specific state '''
        endpoints = []
        sdnc = SDNConnect()
        sdnc.get_stored_endpoints()
        for endpoint in sdnc.endpoints:
            # TODO parse out args instead of all endpoints
            endpoints.append(endpoint)
        return endpoints

    def show_devices(self, args):
        ''' show all devices that are of a specific filter. i.e. windows, dev workstation, etc.'''
        return


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

    @staticmethod
    def completion(text, line, completions):
        # TODO handle expectation of '?'
        if line.endswith('?'):
            pass

        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in completions if s.lower().startswith(mline.lower())]

    def do_what(self, arg):
        '''
        Find out what something is:
        WHAT IS 10.0.0.1
        WHAT IS 18:EF:02:2D:49:00
        '''
        Commands().what_is(arg)

    def complete_what(self, text, line, begidx, endidx):
        return PoseidonShell.completion(text, line, self.what_completions)

    def do_where(self, arg):
        '''
        Find out where something is:
        WHERE IS 10.0.0.1
        WHERE IS 18:EF:02:2D:49:00
        '''
        Commands().where_is(arg)

    def do_collect(self, arg):
        '''
        Collect on something on the network:
        COLLECT ON 10.0.0.1 FOR 300 SECONDS
        COLLECT ON 18:EF:02:2D:49:00 FOR 5 MINUTES
        '''
        Commands().collect_on(arg)

    def do_show(self, arg):
        '''
        Show things on the network based on filters:
        SHOW ACTIVE DEVICES
        SHOW INACTIVE DEVICES
        '''
        # TODO check if it should call show_state or show_devices
        endpoints = Commands().show_state(arg)
        print(endpoints)

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
