import cmd


class Commands:

    def what_is(self, args):
        return

    def where_is(self, args):
        return

    def collect_on(self, args):
        return


class PoseidonShell(cmd.Cmd):
    intro = 'Welcome to the Poseidon shell. Type help or ? to list commands.\n'
    prompt = '\033[1;32mposeidon$ \033[1;m'
    file = None

    def do_what(self, arg):
        '''
        Find out what something is:
        WHAT IS 10.0.0.1
        WHAT IS 18:EF:02:2D:49:00
        '''
        Commands().what_is(arg)

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


if __name__ == '__main__':
    PoseidonShell().cmdloop()
