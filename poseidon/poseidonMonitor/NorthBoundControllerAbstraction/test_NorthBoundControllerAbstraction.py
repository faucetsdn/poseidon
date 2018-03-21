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
Test module for NorthBoundControllerAbstraction.py

Created on 28 June 2016
@author: dgrossman
"""

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import controller_interface
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import Update_Switch_State
from poseidon.poseidonMonitor.endPoint import EndPoint
import json

module_logger = Logger.logger


def make_endpoint_dict(e_dict, my_hash, state, data):
    ''' make a new endpoint '''
    e_dict[my_hash] = EndPoint(data, state=state)


def test_update_endpoint_state():

    class mybcf():

        def __init__(self):
            pass

        def format_endpoints(self, data):
            a = [{'ip-address': '10.0.0.1',
                  'mac': 'f8:b1:56:fe:f2:de',
                  'segment': 'prod',
                  'tenant': 'FLOORPLATE',
                  'name': None},
                 {'ip-address': '10.0.0.2',
                  'mac': '20:4c:9e:5f:e3:c3',
                  'segment': 'to-core-router',
                  'tenant': 'EXTERNAL',
                  'name': None}]

            return a

        def get_endpoints(self, messages=None):
            pass

    uss = controller_interface.get_endpoint('Update_Switch_State')
    uss.sdnc = mybcf()
    output = json.loads(uss.update_endpoint_state())
    correct_output = json.loads(
        '{"service": "NorthBoundControllerAbstraction:Update_Switch_State", "times": 0, "machines": [{"ip-address": "10.0.0.1", "mac": "f8:b1:56:fe:f2:de", "segment": "prod", "tenant": "FLOORPLATE", "name": null}, {"ip-address": "10.0.0.2", "mac": "20:4c:9e:5f:e3:c3", "segment": "to-core-router", "tenant": "EXTERNAL", "name": null}], "resp": "ok"}')
    assert str(output) == str(correct_output)


def test_find_new_machines_first_time():
    uss = Update_Switch_State()
    uss.first_time = True
    machines = [{'ip-address': '10.0.0.101',
                 'mac': 'f8:b1:56:fe:f2:de',
                 'segment': 'prod',
                 'tenant': 'FLOORPLATE',
                 'name': None},
                {'ip-address': '10.0.0.99',
                 'mac': '20:4c:9e:5f:e3:c3',
                 'segment': 'to-core-router',
                 'tenant': 'EXTERNAL',
                 'name': None}]
    uss.find_new_machines(machines)
    answer = dict(
        {
            "d502caea3609d553ab16a00c554f0602c1419f58": {
                "state": "KNOWN",
                "next-state": "NONE",
                "endpoint": {
                    "ip-address": "10.0.0.101",
                    "mac": "f8:b1:56:fe:f2:de",
                    "segment": "prod",
                    "tenant": "FLOORPLATE",
                    "name": None}},
            "3da53a95ae5d034ae37b539a24370260a36f8bb2": {
                "state": "KNOWN",
                "next-state": "NONE",
                "endpoint": {
                    "ip-address": "10.0.0.99",
                    "mac": "20:4c:9e:5f:e3:c3",
                    "segment": "to-core-router",
                    "tenant": "EXTERNAL",
                    "name": None}}})
    #assert str(answer) == str(dict(uss.endpoint_states))
    for key in answer:
        assert answer[key]['state'] == uss.endpoints.state[key].state
        for next_key in answer[key]['endpoint']:
            assert answer[key]['endpoint'][next_key] == uss.endpoints.state[key].endpoint_data[next_key]


def test_file_new_machines_later():
    uss = Update_Switch_State()
    uss.first_time = False
    machines = [{'ip-address': '10.0.0.101',
                 'mac': 'f8:b1:56:fe:f2:de',
                 'segment': 'prod',
                 'tenant': 'FLOORPLATE',
                 'name': None},
                {'ip-address': '10.0.0.99',
                 'mac': '20:4c:9e:5f:e3:c3',
                 'segment': 'to-core-router',
                 'tenant': 'EXTERNAL',
                 'name': None}]
    answer = dict(
        {
            'd502caea3609d553ab16a00c554f0602c1419f58': {
                'state': 'UNKNOWN',
                'next-state': 'NONE',
                'endpoint': {
                    'ip-address': '10.0.0.101',
                    'mac': 'f8:b1:56:fe:f2:de',
                    'segment': 'prod',
                    'tenant': 'FLOORPLATE',
                    'name': None}},
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': {
                'state': 'UNKNOWN',
                'next-state': 'NONE',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}}})
    uss.find_new_machines(machines)

    #assert str(answer) == str(dict(uss.endpoint_states))
    for key in answer:
        assert answer[key]['state'] == uss.endpoints.state[key].state
        assert answer[key]['next-state'] == uss.endpoints.state[key].next_state
        for key2 in answer[key]['endpoint']:
            assert answer[key]['endpoint'][key2] == uss.endpoints.state[key].endpoint_data[key2]


def test_unmirror_endpoint():
    class Mock_bcf():

        def __init__(self):
            pass

        def unmirror_ip(self, my_ip, messages=None):
            assert my_ip == '10.0.0.99'

    uss = Update_Switch_State()
    uss.first_time = False
    uss.sdnc = Mock_bcf()
    machines = [{'ip-address': '10.0.0.101',
                 'mac': 'f8:b1:56:fe:f2:de',
                 'segment': 'prod',
                 'tenant': 'FLOORPLATE',
                 'name': None},
                {'ip-address': '10.0.0.99',
                 'mac': '20:4c:9e:5f:e3:c3',
                 'segment': 'to-core-router',
                 'tenant': 'EXTERNAL',
                 'name': None}]
    uss.find_new_machines(machines)

    assert uss.unmirror_endpoint('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    assert not uss.unmirror_endpoint(
        '4da53a95ae5d034ae37b539a24370260a36f8bb2')


def test_get_endpoint_state():
    class Mock_bcf():

        def __init__(self):
            pass

    uss = Update_Switch_State()
    uss.first_time = False
    uss.sdnc = Mock_bcf()
    machines = [{'ip-address': '10.0.0.101',
                 'mac': 'f8:b1:56:fe:f2:de',
                 'segment': 'prod',
                 'tenant': 'FLOORPLATE',
                 'name': None},
                {'ip-address': '10.0.0.99',
                 'mac': '20:4c:9e:5f:e3:c3',
                 'segment': 'to-core-router',
                 'tenant': 'EXTERNAL',
                 'name': None}]
    uss.find_new_machines(machines)
    retval = uss.endpoints.get_endpoint_state('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    answer = 'UNKNOWN'
    assert retval == answer

    retval = uss.endpoints.get_endpoint_state('NOT-A-HASH')
    answer = None
    assert retval == answer


def test_get_endpoint_ip():
    class Mock_bcf():

        def __init__(self):
            pass

    uss = Update_Switch_State()
    uss.first_time = False
    uss.sdnc = Mock_bcf()
    machines = [{'ip-address': '10.0.0.101',
                 'mac': 'f8:b1:56:fe:f2:de',
                 'segment': 'prod',
                 'tenant': 'FLOORPLATE',
                 'name': None},
                {'ip-address': '10.0.0.99',
                 'mac': '20:4c:9e:5f:e3:c3',
                 'segment': 'to-core-router',
                 'tenant': 'EXTERNAL',
                 'name': None}]
    uss.find_new_machines(machines)
    retval = uss.endpoints.get_endpoint_ip('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    answer = '10.0.0.99'
    assert retval == answer

    retval = uss.endpoints.get_endpoint_ip('NOT-A-HASH')
    answer = None
    assert retval == answer


def test_change_endpoint_state():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'KNOWN'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    answer = dict(
        {
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': {
                'state': 'TEST_STATE',
                'next-state': 'NONE',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}}})
    uss.endpoints.change_endpoint_state(
        '3da53a95ae5d034ae37b539a24370260a36f8bb2', new_state='TEST_STATE')
    #assert str(answer) == str(dict(uss.endpoint_states))
    for key in answer:
        assert answer[key]['state'] == uss.endpoints.state[key].state
        assert answer[key]['next-state'] == uss.endpoints.state[key].next_state
        for key2 in answer[key]['endpoint']:
            assert answer[key]['endpoint'][key2] == uss.endpoints.state[key].endpoint_data[key2]


def test_change_endpoint_nextstate():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'KNOWN'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    answer = dict(
        {
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': {
                'state': 'KNOWN',
                'next-state': 'TEST_STATE',
                'endpoint': {
                    'ip-address': '10.0.0.99',
                    'mac': '20:4c:9e:5f:e3:c3',
                    'segment': 'to-core-router',
                    'tenant': 'EXTERNAL',
                    'name': None}}})
    uss.endpoints.change_endpoint_nextstate(
        '3da53a95ae5d034ae37b539a24370260a36f8bb2', next_state='TEST_STATE')
    #assert str(answer) == str(dict(uss.endpoint_states))
    for key in answer:
        assert answer[key]['state'] == uss.endpoints.state[key].state
        assert answer[key]['next-state'] == uss.endpoints.state[key].next_state
        for key2 in answer[key]['endpoint']:
            assert answer[key]['endpoint'][key2] == uss.endpoints.state[key].endpoint_data[key2]


def test_get_endpoinit_next():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'KNOWN'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    next_state = uss.endpoints.get_endpoint_next(
        '3da53a95ae5d034ae37b539a24370260a36f8bb2')

    assert 'NONE' == next_state

    next_state = uss.endpoints.get_endpoint_next('NOT-A-HASH')
    assert next_state is None


def test_get_endpoinit_state():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'TEST_STATE'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    next_state = uss.endpoints.get_endpoint_state(
        '3da53a95ae5d034ae37b539a24370260a36f8bb2')

    assert 'TEST_STATE' == next_state


def test_return_endpoint_state():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'TEST_STATE'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    answer = dict(
        {
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='TEST_STATE', next_state='NONE')

        })
    eps = uss.return_endpoint_state()
    key = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    assert eps.state[key].state == answer[key].state
    assert eps.state[key].next_state == answer[key].next_state
    for key2 in eps.state[key].endpoint_data:
        assert eps.state[key].endpoint_data[key2] == answer[key].endpoint_data[key2]

    #assert str(answer) == str(dict(uss.return_endpoint_state()))
    #assert uss.return_endpoint_state() == uss.endpoint_states


def test_first_run_bcf():

    uss = Update_Switch_State()
    uss.mod_configuration = dict()
    uss.mod_configuration['controller_uri'] = 'TEST_URI'
    uss.mod_configuration['controller_user'] = 'TEST_USER'
    uss.mod_configuration['controller_pass'] = 'TEST_PASS'
    uss.mod_configuration['controller_type'] = 'bcf'

    uss.configured = True
    uss.first_run()
    assert uss.controller['URI'] == 'TEST_URI'
    assert uss.controller['USER'] == 'TEST_USER'
    assert uss.controller['PASS'] == 'TEST_PASS'
    assert uss.controller['TYPE'] == 'bcf'

    uss = Update_Switch_State()
    uss.configured = False
    uss.first_run()

 


def test_first_run_faucet():

    uss = Update_Switch_State()
    uss.mod_configuration = dict()
    uss.mod_configuration['controller_type'] = 'faucet'
    uss.mod_configuration['controller_uri'] = 'localhost'
    uss.mod_configuration['controller_pass'] = 'TEST_PASS'
    uss.mod_configuration['controller_user'] = 'self'
    uss.mod_configuration['controller_config_file'] = '/etc/faucet/faucet.yaml'
    uss.mod_configuration['controller_log_file'] = '/var/log/faucet/faucet.log'
    uss.mod_configuration['controller_mirror_ports'] = '{"0xdeadbeef":"port1"}'

    uss.configured = True
    uss.first_run()
    assert uss.controller['TYPE'] == 'faucet'
    assert uss.controller['URI'] == 'localhost'
    assert uss.controller['USER'] == 'self'
    assert uss.controller['PASS'] == 'TEST_PASS'
    assert uss.controller['CONFIG_FILE'] == '/etc/faucet/faucet.yaml'
    assert uss.controller['LOG_FILE'] == '/var/log/faucet/faucet.log'
    assert uss.controller['MIRROR_PORTS'] == {'0xdeadbeef': 'port1'}


def test_first_run_unknown():

    uss = Update_Switch_State()
    uss.mod_configuration = dict()
    uss.mod_configuration['controller_type'] = 'dummy'

    uss.configured = True
    uss.first_run()
    assert uss.controller['TYPE'] == 'dummy'


def test_shutdown_endpoint():
    class Mockbcf():

        def __init__(self):
            pass

        def shutdown_ip(self, ip):
            assert ip == '10.0.0.99'

    uss = Update_Switch_State()
    uss.sdnc = Mockbcf()
    stuff = dict(
        {
            'd502caea3609d553ab16a00c554f0602c1419f58': EndPoint({
                'ip-address': '10.0.0.101',
                'mac': 'f8:b1:56:fe:f2:de',
                'segment': 'prod',
                'tenant': 'FLOORPLATE',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='NONE'),
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='KNOWN', next_state='NONE')

        })
    for s in stuff:
        uss.endpoints.state[s] = stuff[s]

    ret_val = uss.shutdown_endpoint('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    assert ret_val
    ret_val = uss.shutdown_endpoint('NOT_A_HASH')
    assert not ret_val


def test_mirror_endpoint():
    class Mockbcf():

        def __init__(self):
            pass

        def mirror_ip(self, ip, messages=None):
            assert ip == '10.0.0.99'

    uss = Update_Switch_State()
    uss.sdnc = Mockbcf()
    stuff = dict(
        {
            'd502caea3609d553ab16a00c554f0602c1419f58': EndPoint({
                'ip-address': '10.0.0.101',
                'mac': 'f8:b1:56:fe:f2:de',
                'segment': 'prod',
                'tenant': 'FLOORPLATE',
                'name': None},
                prev_state='NONE', state='UNKNOWN', next_state='NONE'),
            '3da53a95ae5d034ae37b539a24370260a36f8bb2': EndPoint({
                'ip-address': '10.0.0.99',
                'mac': '20:4c:9e:5f:e3:c3',
                'segment': 'to-core-router',
                'tenant': 'EXTERNAL',
                'name': None},
                prev_state='NONE', state='KNOWN', next_state='NONE'),

        })
    for s in stuff:
        uss.endpoints.state[s] = stuff[s]

    ret_val = uss.mirror_endpoint('3da53a95ae5d034ae37b539a24370260a36f8bb2')
    assert ret_val
    ret_val = uss.mirror_endpoint('NOT_A_HASH')
    assert not ret_val


def test_print_endpoint_state():
    uss = Update_Switch_State()
    uss.first_time = False
    endpoint_data = dict({'ip-address': '10.0.0.99',
                          'mac': '20:4c:9e:5f:e3:c3',
                          'segment': 'to-core-router',
                          'tenant': 'EXTERNAL',
                          'name': None})
    hash_value = '3da53a95ae5d034ae37b539a24370260a36f8bb2'
    state = 'TEST_STATE'
    make_endpoint_dict(uss.endpoints.state, hash_value, state, endpoint_data)
    uss.endpoints.print_endpoint_state()
