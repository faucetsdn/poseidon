# -*- coding: utf-8 -*-
"""
Test module for faucet parser.
@author: Charlie Lewis
"""
import os

from poseidon.controllers.faucet.parser import Parser


def test_Parser():
    """
    Tests Parser
    """
    config_dir = '/etc/faucet'
    log_dir = '/var/log/faucet'
    if not os.path.exists(config_dir):
        config_dir = os.path.join(os.getcwd(), 'faucet')
    if not os.path.exists(log_dir):
        log_dir = os.path.join(os.getcwd(), 'faucet')
    parser = Parser(mirror_ports={'switch1': 3})
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'mirror', 1, 'switch1')
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'mirror', 2, 0x70b3d56cd32e)
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'mirror', 2, 'switch1')
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'mirror', 5, 'switch1')
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'mirror', 6, 'bad')
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'unmirror', None, None)
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'shutdown', None, None)
    parser.config(os.path.join(config_dir, 'faucet.yaml'),
                  'unknown', None, None)
    parser.log(os.path.join(log_dir, 'faucet.log'))
