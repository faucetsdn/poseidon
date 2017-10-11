#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.poseidonMonitor import Monitor
from poseidon.poseidonMonitor import poseidonMonitor
from poseidon.poseidonMonitor.poseidonMonitor import schedule_job_kickurl
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
    # signal handler seem to simply exit and kill all the jobs no matter what
    # we pass
    mock_monitor.signal_handler(None, None)
    assert ['job1 cancelled', 'job2 cancelled',
            'job3 cancelled'] == mock_monitor.schedule.call_log
    assert True == mock_monitor.rabbit_channel_connection_local.connection_closed


def test_start_vent_collector():
    class requests():

        @staticmethod
        def post(uri, json):
            def mock_response(): return None
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


def test_get_rabbit_message():
    poseidonMonitor.CTRL_C = False


def test_rabbit_callback():
    def mock_method(): return None
    mock_method.routing_key = "test_routing_key"

    class MockQueue:
        item = None

        def put(self, item):
            self.item = item
            return True

        # used for testing to verify that we put right stuff there
        def get_item(self):
            return self.item

    mock_queue = MockQueue()
    poseidonMonitor.rabbit_callback(
        "Channel",
        mock_method,
        "properties",
        "body",
        mock_queue)
    assert mock_queue.get_item() == (mock_method.routing_key, "body")


def test_schedule_job_reinvestigation():
    end_points = {
        "hash_0": {"state": "REINVESTIGATING", "next-state": "UNKNOWN"},
        "hash_1": {"state": "UNKNOWN", "next-state": "REINVESTIGATING"},
        "hash_2": {"state": "known", "next-state": "UNKNOWN"}
    }
    poseidonMonitor.schedule_job_reinvestigation(2, end_points, module_logger)


def test_print_endpoint_state():
    class MockMonitor(Monitor):
        # no need to init the monitor

        def __init__(self):
            pass

    mock_monitor = MockMonitor()
    mock_monitor.logger = module_logger
    test_dict_to_return = {'test': True}
    item = ('poseidon.algos.ML.results', json.dumps(test_dict_to_return))
    assert test_dict_to_return == mock_monitor.get_rabbit_message(item)
    end_points = {
        "hash_0": {
            "state": "REINVESTIGATING",
            "next-state": "UNKNOWN",
            "endpoint": "test1"},
        "hash_1": {
            "state": "UNKNOWN",
            "next-state": "REINVESTIGATING",
            "endpoint": "test2"},
        "hash_2": {
            "state": "known",
            "next-state": "UNKNOWN",
            "endpoint": "test3"}}
    mock_monitor = MockMonitor()
    mock_monitor.logger = module_logger
    mock_monitor.print_endpoint_state(end_points)


def test_configSelf():
    class MockMonitor(Monitor):
        mod_name = 'testingConfigSelf'

        mod_configuration = [1, 2, 3, 4]

        # no need to init the monitor
        def __init__(self):
            pass

    class MockSectionConfig:

        def direct_get(self, mod_name):
            assert "testingConfigSelf" == mod_name
            return [(1, "YOYO")]

    class MockConfig():

        def get_endpoint(self, endpoint_type):
            assert "Handle_SectionConfig" == endpoint_type
            section_conf = MockSectionConfig()
            return section_conf

    mock_monitor = MockMonitor()
    mock_monitor.Config = MockConfig()
    mock_monitor.logger = module_logger
    mock_monitor.configSelf()
    assert mock_monitor.mod_configuration[1] == "YOYO"


def test_update_next_state():

    class Mock_Update_Switch_State():

        def __init__(self):
            self.endpoints = dict({'4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': {'state': 'UNKNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.00.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None}},
                                   'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': {'state': 'KNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}}})

        def return_endpoint_state(self):
            return self.endpoints

    class MockMonitor(Monitor):

        def __init__(self):
            self.uss = Mock_Update_Switch_State()

    monitor = MockMonitor()
    monitor.update_next_state(
        {'d60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': 'TESTSTATE'})
    correct_answer = dict({'4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': {'state': 'UNKNOWN', 'next-state': 'MIRRORING', 'endpoint': {'ip-address': '10.00.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None}},
                           'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': {'state': 'KNOWN', 'next-state': 'TESTSTATE', 'endpoint': {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}}})
    assert str(correct_answer) == str(monitor.uss.return_endpoint_state())


def test_configSelf():
    class MockMonitor(Monitor):
        def __init__(self):
            self.mod_name = None
            self.mod_configuration = dict()
            pass

    class MockConfig():
        def __init__(self):
            pass

        def get_endpoint(self, sectionType):
            return MockConfig()

        def direct_get(self, name):
            ret_val = dict()
            ret_val[1] = 'one'
            ret_val[2] = 'two'
            ret_val[3] = 'three'
            return [(x, ret_val[x]) for x in ret_val]

    class MockLogger():
        def __init__(self):
            pass

        def debug(self, words):
            pass

    monitor = MockMonitor()
    monitor.logger = MockLogger()
    monitor.Config = MockConfig()

    monitor.configSelf()

    answer = dict({1: 'one', 2: 'two', 3: 'three'})

    assert str(answer) == str(dict(monitor.mod_configuration))


def test_schedule_job_kickurl():
    
    class MockLogger():
        def __init__(self):
            pass

        def debug(self,logline):
            pass

    
    class helper():
        def __init__(self):
            pass
            
        def update_endpoint_state(self):
            pass

    class MockNorthBoundControllerAbstraction():
        def __init__(self):
            pass

        def get_endpoint(self,some_word):
            return helper()

    class func():
        def __init__(self):
            self.NorthBoundControllerAbstraction = MockNorthBoundControllerAbstraction()
            pass

    schedule_job_kickurl(func(),MockLogger())