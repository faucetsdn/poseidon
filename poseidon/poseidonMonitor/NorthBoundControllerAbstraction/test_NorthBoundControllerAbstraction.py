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
Test module for NorthBoundControllerAbstraction.py

Created on 28 June 2016
@author: dgrossman
"""

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import controller_interface
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import Update_Switch_State
import json

module_logger = Logger.logger


def test_update_endpoint_state():

    class mybcf():
        def __init__(self):
            pass

        def format_endpoints(self, data):
            a = [{'ip-address': '10.0.0.1', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None},
                 {'ip-address': '10.0.0.2', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}]

            return a

        def get_endpoints(self):
            pass

    uss = controller_interface.get_endpoint('Update_Switch_State')
    uss.bcf = mybcf()
    output = json.loads(uss.update_endpoint_state())
    correct_output = json.loads(
        '{"service": "NorthBoundControllerAbstraction:Update_Switch_State", "times": 0, "machines": [{"ip-address": "10.0.0.1", "mac": "f8:b1:56:fe:f2:de", "segment": "prod", "tenant": "FLOORPLATE", "name": null}, {"ip-address": "10.0.0.2", "mac": "20:4c:9e:5f:e3:c3", "segment": "to-core-router", "tenant": "EXTERNAL", "name": null}], "resp": "ok"}')
    assert str(output) == str(correct_output)


def test_find_new_machines_first_time():
    uss = Update_Switch_State()
    uss.first_time = True
    machines = [{'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None},
                {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}]
    uss.find_new_machines(machines)
    answer = dict({"d502caea3609d553ab16a00c554f0602c1419f58": {"state": "KNOWN", "next-state": "NONE", "endpoint": {"ip-address": "10.0.0.101", "mac": "f8:b1:56:fe:f2:de", "segment": "prod", "tenant": "FLOORPLATE", "name": None}},
                   "3da53a95ae5d034ae37b539a24370260a36f8bb2": {"state": "KNOWN", "next-state": "NONE", "endpoint": {"ip-address": "10.0.0.99", "mac": "20:4c:9e:5f:e3:c3", "segment": "to-core-router", "tenant": "EXTERNAL", "name": None}}})
    assert str(answer) == str(dict(uss.endpoint_states))


def test_file_new_machines_later():
    uss = Update_Switch_State()
    uss.first_time = False
    machines = [{'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None},
                {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}]
    answer = dict({'d502caea3609d553ab16a00c554f0602c1419f58': {'state': 'UNKNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None}},
                   '3da53a95ae5d034ae37b539a24370260a36f8bb2': {'state': 'UNKNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}}})
    uss.find_new_machines(machines)
    assert str(answer) == str(dict(uss.endpoint_states))


def test_make_known_endpoint():
    class Mock_bcf():
        def __init__(self):
            pass

        def unmirror_ip(self, my_ip):
            assert my_ip == '10.0.0.99'

    uss = Update_Switch_State()
    uss.first_time = False
    uss.bcf = Mock_bcf()
    machines = [{'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None},
                {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}]
    uss.find_new_machines(machines)

    uss.make_known_endpoint('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    answer = dict({'d502caea3609d553ab16a00c554f0602c1419f58': {'state': 'UNKNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de', 'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None}},
                   '3da53a95ae5d034ae37b539a24370260a36f8bb2': {'state': 'KNOWN', 'next-state': 'NONE', 'endpoint': {'ip-address': '10.0.0.99', 'mac': '20:4c:9e:5f:e3:c3', 'segment': 'to-core-router', 'tenant': 'EXTERNAL', 'name': None}}})
    assert str(answer) == str(dict(uss.endpoint_states))
