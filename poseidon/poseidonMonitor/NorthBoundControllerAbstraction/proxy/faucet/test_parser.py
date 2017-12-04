#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Test module for faucet parser.

@author: cglewis
"""
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.parser import Parser


def test_Parser():
    """
    Tests Parser
    """
    parser = Parser(mirror_ports={'switch1':3})
    parser.config('/etc/ryu/faucet/faucet.yaml', 'mirror', 1, '0x70b3d56cd32e')
    parser.config('/etc/ryu/faucet/faucet.yaml', 'mirror', 2, 0x70b3d56cd32e)
    parser.config('/etc/ryu/faucet/faucet.yaml', 'mirror', 2, '0x70b3d56cd32e')
    parser.config('/etc/ryu/faucet/faucet.yaml', 'mirror', 5, '0x70b3d56cd32e')
    parser.config('/etc/ryu/faucet/faucet.yaml', 'mirror', 6, 'bad')
    parser.config('/etc/ryu/faucet/faucet.yaml', 'unmirror', None, None)
    parser.config('/etc/ryu/faucet/faucet.yaml', 'shutdown', None, None)
    parser.config('/etc/ryu/faucet/faucet.yaml', 'unknown', None, None)
    parser.log('/var/log/ryu/faucet/faucet.log')
