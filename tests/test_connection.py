# -*- coding: utf-8 -*-
"""
Test module for faucet connection.
@author: Charlie Lewis
"""
from poseidon.controllers.faucet.connection import Connection


def test_Connection():
    """
    Tests Connection
    """
    conn = Connection(host='foo')
    conn._connect()
    conn._disconnect()
    conn.exec_command('foo')
    conn.receive_file('config')
    conn.receive_file('log')
    conn.send_file('config')
    conn.send_file('log')
    conn = Connection()
    conn.exec_command('foo')
    conn.receive_file('config')
    conn.receive_file('log')
    conn.send_file('config')
    conn.send_file('log')
