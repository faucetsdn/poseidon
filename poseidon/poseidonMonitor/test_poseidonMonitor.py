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
Test module for poseidonMonitor.py

Created on 28 June 2016
@author: dgrossman, MShel
"""

import json

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor import poseidonMonitor
from poseidon.poseidonMonitor.endPoint import EndPoint
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.EndpointWrapper import Endpoint_Wrapper
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import \
    BcfProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet.faucet import \
    FaucetProxy

from poseidon.poseidonMonitor.poseidonMonitor import (CTRL_C, Monitor,
                                                      Collector,
                                                      schedule_job_kickurl,
                                                      schedule_thread_worker)


def test_signal_handler():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

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
    mock_monitor.logger = MockLogger()

    # signal handler seem to simply exit and kill all the jobs no matter what
    # we pass

    mock_monitor.signal_handler(None, None)
    assert ['job1 cancelled', 'job2 cancelled',
            'job3 cancelled'] == mock_monitor.schedule.call_log
    assert True == mock_monitor.rabbit_channel_connection_local.connection_closed

def test_start_vent_collector():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class requests():

        def __init__(self):
            pass

        def post(uri, json, data):
            def mock_response(): return None
            mock_response.text = "success"
            # cover object
            a = mock_response()
            assert a is None
            assert mock_response.text == "success"
            return mock_response

    poseidonMonitor.CTRL_C['STOP'] = False
    poseidonMonitor.requests = requests()

    class Mock_Update_Switch_State():

        def __init__(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),

                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE')
                })

            self.endpoints = Endpoint_Wrapper()

            for s in stuff:
                self.endpoints.state[s] = stuff[s]

            self.logger = None

            self.sdnc = FaucetProxy()

        def return_endpoint_state(self):
            return self.endpoints

    class MockMonitor(Monitor):

        def __init__(self):

            self.mod_configuration = dict({
                'collector_interval': 900,
                'collector_nic': 2,
                'vent_ip': '0.0.0.0',
                'vent_port': '8080',
            })

            self.uss = Mock_Update_Switch_State()

    mock_monitor = MockMonitor()
    mock_monitor.logger = MockLogger()
    dev_hash = 'test'
    num_cuptures = 3
    mock_monitor.start_vent_collector(dev_hash, num_cuptures)

def test_get_vent_collectors():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class requests():

        def __init__(self):
            pass

        def get(self, uri):
            def mock_response():
                def mock_json(): return {'dataset': []}
                mock_response.json = mock_json
                return None
            mock_response.text = ("(True, [{'status': u'exited', 'args': [u'enp3s0',"
            " u'900', u'd525bec2b05a12af95021337eaa0b20e02b70f3a', u'1', "
            "u'host 192.168.0.30'], 'id': u'0bce1351109e'}, {'status': u'exited', "
            "'args': [u'enp3s0', u'900', u'97b7edfa648a994467ff0d2f87858a5ea22adaaa', "
            "u'1', u'host 192.168.0.20'], 'id': u'c1a662efea1c'}, {'status': u'exited', "
            "'args': [u'enp3s0', u'900', u'5a348c8a714c1092c7401decc74dbca5f5749195', "
            "u'1', u'host 192.168.0.50'], 'id': u'2602280bb9da'}])")
            # cover object
            a = mock_response()
            b = mock_response.json()
            assert a is None
            assert isinstance(b, dict)
            return mock_response

    poseidonMonitor.CTRL_C['STOP'] = False
    poseidonMonitor.requests = requests()

    class Mock_Update_Switch_State():

        def __init__(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),

                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE')
                })

            self.endpoints = Endpoint_Wrapper()

            for s in stuff:
                self.endpoints.state[s] = stuff[s]

            self.logger = None

    class MockMonitor(Monitor):

        def __init__(self):

            self.mod_configuration = dict({
                'collector_interval': 900,
                'collector_nic': 2,
                'vent_ip': '0.0.0.0',
                'vent_port': '8080',
            })

            self.uss = Mock_Update_Switch_State()

    mock_monitor = MockMonitor()
    mock_monitor.logger = MockLogger()
    result = mock_monitor.get_vent_collectors()
    assert isinstance(result, dict)

def test_host_has_active_collectors_false():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class requests():

        def __init__(self):
            pass

        def get(self, uri):
            def mock_response():
                def mock_json(): return {'dataset': []}
                mock_response.json = mock_json
                return None
            mock_response.text = ("(True, [{'status': u'exited', 'args': [u'enp3s0',"
            " u'900', u'test0', u'1', "
            "u'host 192.168.0.30'], 'id': u'0bce1351109e'}, {'status': u'exited', "
            "'args': [u'enp3s0', u'900', u'test1', "
            "u'1', u'host 192.168.0.20'], 'id': u'c1a662efea1c'}, {'status': u'exited', "
            "'args': [u'enp3s0', u'900', u'test2', "
            "u'1', u'host 192.168.0.50'], 'id': u'2602280bb9da'}])")
            # cover object
            a = mock_response()
            b = mock_response.json()
            assert a is None
            assert isinstance(b, dict)
            return mock_response

    poseidonMonitor.CTRL_C['STOP'] = False
    poseidonMonitor.requests = requests()

    class Mock_Update_Switch_State():

        def __init__(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),

                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE')
                })

            self.endpoints = Endpoint_Wrapper()

            for s in stuff:
                self.endpoints.state[s] = stuff[s]

            self.logger = None

    class MockMonitor(Monitor):

        def __init__(self):

            self.mod_configuration = dict({
                'collector_interval': 900,
                'collector_nic': 2,
                'vent_ip': '0.0.0.0',
                'vent_port': '8080',
            })

            self.uss = Mock_Update_Switch_State()

    mock_monitor = MockMonitor()
    mock_monitor.logger = MockLogger()
    dev_hash = 'test0'
    result = mock_monitor.host_has_active_collectors(dev_hash)
    assert result == False

def test_host_has_active_collectors_true():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class requests():

        def __init__(self):
            pass

        def get(self, uri):
            def mock_response():
                def mock_json(): return {'dataset': []}
                mock_response.json = mock_json
                return None
            mock_response.text = ("(True, [{'status': u'exited', 'args': [u'enp3s0',"
            " u'900', u'test0', u'1', "
            "u'host 192.168.0.30'], 'id': u'0bce1351109e'}, {'status': u'exited', "
            "'args': [u'enp3s0', u'900', u'test1', "
            "u'1', u'host 192.168.0.30'], 'id': u'c1a662efea1c'}, {'status': u'running', "
            "'args': [u'enp3s0', u'900', u'test2', "
            "u'1', u'host 192.168.0.30'], 'id': u'2602280bb9da'}])")
            # cover object
            a = mock_response()
            b = mock_response.json()
            assert a is None
            assert isinstance(b, dict)
            return mock_response

    poseidonMonitor.CTRL_C['STOP'] = False
    poseidonMonitor.requests = requests()

    class Mock_Update_Switch_State():

        def __init__(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),

                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE')
                })

            self.endpoints = Endpoint_Wrapper()

            for s in stuff:
                self.endpoints.state[s] = stuff[s]

            self.logger = None

    class MockMonitor(Monitor):

        def __init__(self):

            self.mod_configuration = dict({
                'collector_interval': 900,
                'collector_nic': 2,
                'vent_ip': '0.0.0.0',
                'vent_port': '8080',
            })

            self.uss = Mock_Update_Switch_State()

    mock_monitor = MockMonitor()
    mock_monitor.logger = MockLogger()
    dev_hash = 'test0'
    result = mock_monitor.host_has_active_collectors(dev_hash)
    assert result == True

def test_get_q_item():
    class MockMQueue:

        def get(self, block):
            return "Item"

    poseidonMonitor.CTRL_C['STOP'] = False

    class MockMonitor(Monitor):
        # no need to init the monitor

        def __init__(self):
            pass

    mock_monitor = MockMonitor()
    mock_monitor.m_queue = MockMQueue()
    assert (True, "Item") == mock_monitor.get_q_item()

    poseidonMonitor.CTRL_C['STOP'] = True
    mock_monitor.m_queue = MockMQueue()
    assert (False, None) == mock_monitor.get_q_item()


def test_format_rabbit_message():
    poseidonMonitor.CTRL_C['STOP'] = False

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class MockMonitor(Monitor):

        def __init__(self):
            self.fa_rabbit_routing_key = 'foo'

    mockMonitor = MockMonitor()
    mockMonitor.logger = MockLogger()

    data = dict({'Key1': 'Val1'})
    message = ('poseidon.algos.decider', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)

    assert retval == data

    message = (None, json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)

    assert retval == {}


def test_rabbit_callback():
    def mock_method(): return True
    mock_method.routing_key = "test_routing_key"

    # force mock_method coverage
    assert mock_method()

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

    poseidonMonitor.rabbit_callback(
        "Channel",
        mock_method,
        "properties",
        "body",
        None)


def test_schedule_job_reinvestigation():

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    epw = Endpoint_Wrapper()

    stuff = dict(
        {
            '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                'ip-address': '10.00.0.101',
                'mac': 'f8:b1:56:fe:f2:de',
                'segment': 'prod',
                'tenant': 'FLOORPLATE',
                'name': None},
                prev_state='NONE', state='REINVESTIGATING', next_state='UNKNOWN'),
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING'),

            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='KNOWN', next_state='UNKNOWN'),
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING')
        })

    for s in stuff:
        epw.state[s] = stuff[s]

    assert len(epw.state) == 4

    poseidonMonitor.schedule_job_reinvestigation(4, epw, MockLogger())

    epw = Endpoint_Wrapper()

    stuff = dict(
        {
            '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                'ip-address': '10.00.0.101',
                'mac': 'f8:b1:56:fe:f2:de',
                'segment': 'prod',
                'tenant': 'FLOORPLATE',
                'name': None},
                prev_state='NONE', state='REINVESTIGATING', next_state='UNKNOWN'),
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING'),
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='KNOWN', next_state='UNKNOWN'),
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING'),
            'c60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING'),
            'c60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='REINVESTIGATING'),
            'c60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='OTHER-STATE', next_state='UNKNOWN')
        })

    # end_points = {
    #    "hash_0": {"state": "REINVESTIGATING", "next-state": "UNKNOWN"},
    #    "hash_1": {"state": "UNKNOWN", "next-state": "REINVESTIGATING"},
    #    "hash_2": {"state": "KNOWN", "next-state": "UNKNOWN"},
    #    "hash_3": {"state": "UNKNOWN", "next-state": "REINVESTIGATING"},
    #    "hash_4": {"state": "UNKNOWN", "next-state": "REINVESTIGATING"},
    #    "hash_5": {"state": "UNKNOWN", "next-state": "REINVESTIGATING"},
    #    "hash_6": {"state": "OTHER-STATE", "next-state": "UNKNOWN"}
    #}

    for s in stuff:
        epw.state[s] = stuff[s]

    poseidonMonitor.schedule_job_reinvestigation(4, epw, MockLogger())

    epw = Endpoint_Wrapper()
    #end_points = {}
    poseidonMonitor.schedule_job_reinvestigation(4, epw, MockLogger())

    epw.state['4ee39d254db3e4a5264b75ce8ae312d69f9e73a3'] = stuff['4ee39d254db3e4a5264b75ce8ae312d69f9e73a3']
    #end_points = {"hash_0": {"MALFORMED": "YES"}}
    poseidonMonitor.schedule_job_reinvestigation(4, epw, MockLogger())


def test_update_next_state():

    class MockLogger():

        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class Mock_Update_Switch_State():

        def __init__(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),

                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='MIRRORING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='NONE')
                })

            self.endpoints = Endpoint_Wrapper()

            for s in stuff:
                self.endpoints.state[s] = stuff[s]
            self.logger = None

        def return_endpoint_state(self):
            return self.endpoints

    class MockMonitor(Monitor):

        def __init__(self):
            self.uss = None

    monitor = MockMonitor()
    monitor.uss = Mock_Update_Switch_State()
    monitor.logger = MockLogger()
    ml_return = {
        'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': {
            'valid': True, 'classification': {
                'labels': [
                    'Unknown', 'Smartphone', 'Developer workstation'], 'confidences': [
                    0.9983864533039954, 0.0010041873867962805, 0.00042691313815914093]}, 'timestamp': 1508366767.45571, 'decisions': {
                        'investigate': True, 'behavior': 'normal'}},
        'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': {
            'valid': True, 'classification': {
                'labels': [
                    'Unknown', 'Smartphone', 'Developer workstation'], 'confidences': [
                    0.9983864533039954, 0.0010041873867962805, 0.00042691313815914093]}, 'timestamp': 1508366767.45571, 'decisions': {
                'investigate': True, 'behavior': 'abnormal'}},
        'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': {
            'valid': True, 'classification': {
                'labels': [
                    'Unknown', 'Smartphone', 'Developer workstation'], 'confidences': [
                    0.9983864533039954, 0.0010041873867962805, 0.00042691313815914093]}, 'timestamp': 1508366767.45571, 'decisions': {
                'investigate': True, 'behavior': 'normal'}},
        'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': {
            'valid': True, 'classification': {
                'labels': [
                    'Unknown', 'Smartphone', 'Developer workstation'], 'confidences': [
                    0.9983864533039954, 0.0010041873867962805, 0.00042691313815914093]}, 'timestamp': 1508366767.45571, 'decisions': {
                'investigate': True, 'behavior': 'abnormal'}}}

    monitor.update_next_state(ml_return)
    correct_answer = dict(
        {
            '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': {
                'state': 'UNKNOWN',
                'next-state': 'MIRRORING',
                'endpoint': {
                    'ip-address': '10.00.0.101',
                    'mac': 'f8:b1:56:fe:f2:de',
                    'segment': 'prod',
                    'tenant': 'FLOORPLATE',
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': {
                'state': 'MIRRORING',
                'next-state': 'KNOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': {
                'state': 'MIRRORING',
                'next-state': 'SHUTDOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': {
                'state': 'REINVESTIGATING',
                'next-state': 'KNOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': {
                'state': 'REINVESTIGATING',
                'next-state': 'UNKNOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}}})

    eps = monitor.uss.return_endpoint_state().state
    for key in correct_answer:
        assert eps[key].next_state == correct_answer[key]['next-state']

    ml_return = {
        'NOT_FOUND': {
            'valid': True,
            'classification': {
                'labels': [
                    'Unknown',
                    'Smartphone',
                    'Developer workstation'],
                'confidences': [
                    0.9983864533039954,
                    0.0010041873867962805,
                    0.00042691313815914093]},
            'timestamp': 1508366767.45571,
            'decisions': {
                'investigate': True,
                'behavior': 'normal'}}}

    monitor.update_next_state(ml_return)

    ml_return = {
        'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa3': {
            'valid': False,
            'classification': {
                'labels': [
                    'Unknown',
                    'Smartphone',
                    'Developer workstation'],
                'confidences': [
                    0.9983864533039954,
                    0.0010041873867962805,
                    0.00042691313815914093]},
            'timestamp': 1508366767.45571,
            'decisions': {
                'investigate': True,
                'behavior': 'normal'}}}

    monitor.update_next_state(ml_return)


def test_configSelf():
    class MockMonitor(Monitor):

        def __init__(self):
            self.mod_name = None
            self.mod_configuration = dict()

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

        def debug(self, msg):
            pass

    monitor = MockMonitor()
    monitor.logger = MockLogger()
    monitor.Config = MockConfig()

    monitor.configSelf()

    answer = dict({1: 'one', 2: 'two', 3: 'three'})

    assert str(answer) == str(dict(monitor.mod_configuration))


def test_configSelf2():

    class MockMonitor(Monitor):

        def __init__(self):
            self.mod_name = 'testingConfigSelf'
            self.mod_configuration = [1, 2, 3, 4]

    class MockSectionConfig():

        def __init__(self):
            pass

        def direct_get(self, mod_name):
            assert "testingConfigSelf" == mod_name
            return [(1, "YOYO")]

    class MockLogger:
        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class MockConfig():

        def __init__(self):
            pass

        def get_endpoint(self, endpoint_type):
            assert "Handle_SectionConfig" == endpoint_type
            section_conf = MockSectionConfig()
            return section_conf

    mock_monitor = MockMonitor()
    mock_monitor.Config = MockConfig()
    mock_monitor.logger = MockLogger()
    mock_monitor.configSelf()

    assert mock_monitor.mod_configuration[1] == "YOYO"


def test_schedule_job_kickurl():

    class MockLogger():

        def __init__(self):
            pass

        def debug(self, msg):
            pass

        def error(self, msg):
            pass

    class helper():

        def __init__(self):
            pass

        def update_endpoint_state(self, messages=None):
            pass

    class MockNorthBoundControllerAbstraction():

        def __init__(self):
            pass

        def get_endpoint(self, some_word):
            return helper()

    class func():

        def __init__(self):
            self.faucet_event = []
            self.prom_metrics = {}
            self.NorthBoundControllerAbstraction = MockNorthBoundControllerAbstraction()

    schedule_job_kickurl(func(), MockLogger())


def test_Monitor_init():
    monitor = Monitor(skip_rabbit=True)


def test_process():
    from threading import Thread
    import time

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        print('about to go to sleep', CTRL_C)
        time.sleep(5)
        CTRL_C['STOP'] = True
        print('wokefrom sleep', CTRL_C)

    class MockLogger():

        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class MockEndpoint(Endpoint_Wrapper):
        def __init__(self):
            super(MockEndpoint, self).__init__()

        def configSelf(self):
            self.mod_configuration = {
                'vent_ip': '0.0.0.0',
                'vent_port': '8080'
            }

        def makedata(self):
            stuff = dict(
                {
                    '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': EndPoint({
                        'ip-address': '10.00.0.101',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'segment': 'prod',
                        'tenant': 'FLOORPLATE',
                        'active': 1,
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='MIRRORING'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'active': 1,
                        'name': None},
                        prev_state='NONE', state='KNOWN', next_state='REINVESTIGATING'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aab': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'active': 1,
                        'name': None},
                        prev_state='NONE', state='KNOWN', next_state='NONE'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'active': 1,
                        'name': None},
                        prev_state='NONE', state='REINVESTIGATING', next_state='KNOWN'),
                    'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': EndPoint({
                        'ip-address': '10.0.0.99',
                        'mac': '20:4c:9e:5f:e3:c3',
                        'segment': 'to-core-router',
                        'tenant': 'EXTERNAL',
                        'active': 1,
                        'name': None},
                        prev_state='NONE', state='UNKNOWN', next_state='KNOWN')
                })

            for s in stuff:
                self.state[s] = stuff[s]

    class MockUss():

        def __init__(self):
            self.endpoints = MockEndpoint()
            self.endpoints.makedata()

        def return_endpoint_state(self):
            return self.endpoints

    class MockMonitor(Monitor):
        # no need to init the monitor
        def __init__(self):
            self.mod_configuration = {
                'collector_interval': 900,
                'collector_nic': 2,
                'vent_ip': '0.0.0.0',
                'vent_port': '8080'
            }
            self.fa_rabbit_routing_key = 'FAUCET.Event'
            self.faucet_event = None

        def get_q_item(self):
            return (True, ('foo', {}))

        def bad_get_q_item(self):
            return (False, ('bar', {}))

        def format_rabbit_message(self, item):
            return {}

    mock_monitor = MockMonitor()
    mock_monitor.uss = MockUss()
    mock_monitor.logger = MockLogger()

    t1 = Thread(target=thread1)
    t1.start()
    mock_monitor.process()

    t1.join()

    answer = dict(
        {
            '4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': {
                'state': 'UNKNOWN',
                'next-state': 'MIRRORING',
                'endpoint': {
                    'ip-address': '10.00.0.101',
                    'mac': 'f8:b1:56:fe:f2:de',
                    'segment': 'prod',
                    'tenant': 'FLOORPLATE',
                    'active': 1,
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aaa': {
                'state': 'KNOWN',
                'next-state': 'REINVESTIGATING',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'active': 1,
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aab': {
                'state': 'KNOWN',
                'next-state': 'NONE',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'active': 1,
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa1': {
                'state': 'REINVESTIGATING',
                'next-state': 'KNOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'active': 1,
                    'name': None}},
            'd60c5fa5c980b1cd791208eaf62aba9fb46d3aa2': {
                'state': 'UNKNOWN',
                'next-state': 'KNOWN',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'active': 1,
                    'name': None}}
        })

    eps = mock_monitor.uss.endpoints

    for key in answer:
        assert answer[key]['state'] == eps.state[key].state
        assert answer[key]['next-state'] == eps.state[key].next_state

    mock_monitor.get_q_item = mock_monitor.bad_get_q_item

    t1 = Thread(target=thread1)
    t1.start()
    mock_monitor.process()

    t1.join()


def test_schedule_thread_worker():
    from threading import Thread
    import time

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        print('about to go to sleep', CTRL_C)
        time.sleep(5)
        CTRL_C['STOP'] = True
        print('wokefrom sleep', CTRL_C)

    class MockLogger():

        def __init__(self):
            pass

        def debug(self, msg):
            pass

    class mockSchedule():

        def __init__(self):
            pass

        def run_pending(self):
            pass

    class mocksys():

        def __init__(self):
            pass

        # def exit(self):
        #    pass

    sys = mocksys()
    t1 = Thread(target=thread1)
    t1.start()
    try:
        schedule_thread_worker(mockSchedule(), MockLogger())
    except SystemExit:
        pass

    t1.join()
