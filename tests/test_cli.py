# -*- coding: utf-8 -*-
"""
Created on 14 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.cli import PoseidonShell


def test_poseidonshell():
    shell = PoseidonShell()
    shell.do_record('foo.txt')
    shell.do_what('foo')
    shell.complete_show('foo', 'what ok yeah', 0, 1)
    shell.complete_history('foo', 'what ok yeah', 0, 1)
    shell.complete_clear('foo', 'what ok yeah', 0, 1)
    shell.complete_ignore('foo', 'what ok yeah', 0, 1)
    shell.complete_remove('foo', 'what ok yeah', 0, 1)
    shell.complete_show('foo', 'what ok yeah', 0, 1)
    shell.complete_what('foo', 'what ok yeah', 0, 1)
    shell.do_where('foo')
    shell.do_collect('foo')
    shell.do_ignore('foo')
    shell.do_clear('foo')
    shell.do_remove('foo')
    shell.do_history('foo')
    shell.do_show('foo')
    shell.do_quit('foo')
    shell.do_playback('foo.txt')
    shell.precmd('foo')
    shell.close()
    answer = PoseidonShell.completion(
        'what', 'foo what', ['what ok yeah'])
    assert answer == ['what ok yeah']
    fields, sort_by, max_width, unique = shell._check_flags(
        {'fields': ['foo'], 'sort_by': '1', 'max_width': '20'}, ['id'])
    assert unique == False
    assert fields == ['foo']
    assert sort_by == 1
    assert max_width == 20
