# -*- coding: utf-8 -*-
"""
Created on 18 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.commands import Commands
from poseidon.helpers.endpoint import Endpoint


def test_commands():
    commands = Commands()
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    commands.sdnc.endpoints[endpoint.name] = endpoint

    commands.what_is('foo')
    commands.history_of('foo')
    commands.where_is('foo')
    commands.show_devices('foo bar')
    commands.show_devices('all')
    commands.change_devices('foo')
    commands.remove('foo')
    commands.clear_ignored('foo')
    commands.clear_ignored('ignored')
    commands.ignore('foo')
    commands.ignore('inactive')
    commands.remove_inactives('foo')
    commands.remove_ignored('foo')
