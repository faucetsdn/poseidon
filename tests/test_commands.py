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
    commands.show_devices('foo', 'state')
    commands.show_devices('foo', 'role')
    commands.show_devices('foo', 'all')
    commands.show_devices('foo', 'behavior')
    commands.show_devices('foo', 'os')
