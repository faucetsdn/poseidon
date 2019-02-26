# -*- coding: utf-8 -*-
"""
Created on 18 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.commands import Commands


def test_commands():
    commands = Commands()
    commands.what_is('foo')
    commands.history_of('foo')
    commands.where_is('foo')
    commands.show_devices('foo bar')
    commands.show_devices('all')
