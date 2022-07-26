def main():
    import sys
    from poseidon_cli.cli import PoseidonShell
    p_shell = PoseidonShell()
    if '-c' in sys.argv:
        while sys.argv.pop(0) != '-c':
            pass
        p_shell.onecmd(' '.join(sys.argv))
    else:
        p_shell.cmdloop()
