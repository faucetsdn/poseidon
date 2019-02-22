# -*- coding: utf-8 -*-
"""
Created on 14 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.cli import PoseidonShell


def test_poseidonshell():
    shell = PoseidonShell()
    shell.do_record('foo.txt')
    shell.do_show('foo')
    shell.do_quit('foo')
    shell.do_playback('foo.txt')
    shell.precmd('foo')
    shell.close()
