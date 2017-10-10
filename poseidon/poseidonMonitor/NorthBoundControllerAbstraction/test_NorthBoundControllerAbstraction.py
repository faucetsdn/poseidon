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
    correct_output =  json.loads('{"service": "NorthBoundControllerAbstraction:Update_Switch_State", "times": 0, "machines": [{"ip-address": "10.0.0.1", "mac": "f8:b1:56:fe:f2:de", "segment": "prod", "tenant": "FLOORPLATE", "name": null}, {"ip-address": "10.0.0.2", "mac": "20:4c:9e:5f:e3:c3", "segment": "to-core-router", "tenant": "EXTERNAL", "name": null}], "resp": "ok"}')
    assert str(output) == str(correct_output)
