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
Test module for faucet.

@author: cglewis
"""
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.faucet import FaucetProxy


def test_FaucetProxy():
    """
    Tests Faucet
    """
    proxy = FaucetProxy('foo')
    FaucetProxy.format_endpoints("foo")
    proxy.get_endpoints()
    proxy.get_switches()
    proxy.get_span_fabric()
    proxy.get_byip('10.0.0.9')
    proxy.get_bymac('00:00:00:00:12:00')
    proxy.shutdown_ip('10.0.0.9')
    proxy.shutdown_endpoint()
    proxy.get_highest()
    proxy.get_seq_by_ip()
    proxy.mirror_ip()
    proxy.unmirror_ip()
    proxy.mirror_traffic()
