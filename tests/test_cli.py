# -*- coding: utf-8 -*-
"""
Created on 14 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.cli import Commands
from poseidon.cli.cli import PoseidonShell


def test_commands():
    commands = Commands()
    commands.what_is('foo')
    commands.where_is('foo')
    commands.collect_on('foo')


def test_poseidonshell():
    shell = PoseidonShell()
    shell.do_record('foo.txt')
    shell.do_what('foo')
    shell.do_where('foo')
    shell.do_collect('foo')
    shell.do_quit('foo')
    shell.do_playback('foo.txt')
    shell.precmd('foo')
    shell.close()
