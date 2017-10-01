#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
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
Test module for poseidonMonitor.py

Created on 28 June 2016
@author: dgrossman, MShel
"""
import pytest

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.poseidonMonitor import Monitor
from poseidon.poseidonMonitor import poseidonMonitor

module_logger = Logger.logger


def test_start_vent_collector():
    class requests():
        @staticmethod
        def post(uri, json):
            mock_response = lambda: None
            mock_response.text = "success"
            return mock_response

    poseidonMonitor.CTRL_C = False
    poseidonMonitor.requests = requests()

    class MockUSS:
        @staticmethod
        def return_endpoint_state():
            # Really don't care endpoint state here
            return {}

    class MockMonitor(Monitor):
        mod_configuration = {
            'collector_nic': 2,
            'vent_ip': '0.0.0.0',
            'vent_port': '8080',
        }
        uss = MockUSS()

        # no need to init the monitor
        def __init__(self):
            pass

    mock_monitor = MockMonitor()
    mock_monitor.logger = module_logger
    dev_hash = 'test'
    num_cuptures = 3
    mock_monitor.start_vent_collector(dev_hash, num_cuptures)


def test_get_q_item():
    class MockMQueue:
        def get(self, block):
            return "Item"

    poseidonMonitor.CTRL_C = False

    class MockMonitor(Monitor):
        # no need to init the monitor
        def __init__(self):
            pass

    mock_monitor = MockMonitor()
    mock_monitor.m_queue = MockMQueue()
    assert (True, "Item") == mock_monitor.get_q_item()
