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
import json

module_logger = Logger.logger


def test_signal_handler():
    class MockRabbitConnection:
        connection_closed = False

        def close(self):
            self.connection_closed = True
            return True

    class MockMonitor(Monitor):
        # no need to init the monitor
        def __init__(self):
            pass

    class MockScheduele:
        call_log = []

        def __init__(self):
            self.jobs = ['job1', 'job2', 'job3']

        def cancel_job(self, job):
            self.call_log.append(job + ' cancelled')
            return job + ' cancelled'

    mock_monitor = MockMonitor()
    mock_monitor.schedule = MockScheduele()
    mock_monitor.rabbit_channel_connection_local = MockRabbitConnection()
    mock_monitor.logger = module_logger
    # signal handler seem to simply exit and kill all the jobs no matter what we pass
    mock_monitor.signal_handler(None, None)
    assert ['job1 cancelled', 'job2 cancelled', 'job3 cancelled'] == mock_monitor.schedule.call_log
    assert True == mock_monitor.rabbit_channel_connection_local.connection_closed


def test_start_vent_collector():
    class requests():
        @staticmethod
        def post(uri, json):
            mock_response = lambda: None
            mock_response.text = "success"
            return mock_response

    poseidonMonitor.CTRL_C = False
    poseidonMonitor.requests = requests()

    class MockMonitor(Monitor):
        mod_configuration = {
            'collector_nic': 2,
            'vent_ip': '0.0.0.0',
            'vent_port': '8080',
        }

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


def test_get_rabbit_message():
    poseidonMonitor.CTRL_C = False

    class MockMonitor(Monitor):
        # no need to init the monitor
        def __init__(self):
            pass

    mock_monitor = MockMonitor()
    mock_monitor.logger = module_logger
    test_dict_to_return = {'test': True}
    item = ('poseidon.algos.ML.results', json.dumps(test_dict_to_return))
    assert test_dict_to_return == mock_monitor.get_rabbit_message(item)
