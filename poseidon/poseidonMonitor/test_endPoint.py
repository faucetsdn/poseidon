#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Test module for endPoint.py

Created on 2 October 2017
@author: Jorissss
"""
from mock import *
from datetime import datetime, timedelta
import time # so we can override time.time

from poseidon.poseidonMonitor import endPoint

mock_time = Mock()
mock_time.return_value = time.mktime(datetime(2011, 6, 21).timetuple())

test_data = {u'tenant': u'FLOORPLATE',
             u'mac': u'de:ad:be:ef:7f:12',
             u'segment': u'prod',
             u'name': None,
             u'ip-address': u'102.179.20.100'}


def is_same(e1, e2):
    assert e1.state == e2.state
    assert e1.next_state == e2.next_state

    for k in e1.endpoint_data:
        assert e1.endpoint_data[k] == e2.endpoint_data[k]

    for k in e2.endpoint_data:
        assert e1.endpoint_data[k] == e2.endpoint_data[k]


def test_endpoint_creation_no_state():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint2 = endPoint.EndPoint.from_json(endpoint1.to_json())

    is_same(endpoint1, endpoint2)

    assert endpoint1.make_hash() == endpoint2.make_hash()


def test_endpoint_creation_with_state():
    time.time = mock_time
    endpoint0 = endPoint.EndPoint(test_data)
    endpoint1 = endPoint.EndPoint(test_data, state='TEST1')
    endpoint2 = endPoint.EndPoint(test_data, next_state='TEST2')
    endpoint3 = endPoint.EndPoint(test_data, state='TEST1', next_state='TEST2')
    assert "'prev_state': 'None', 'state': 'NONE', 'next_state': 'NONE', 'transition_time': '1308614400.0'" in endpoint0.to_str()
    assert "'prev_state': 'None', 'state': 'TEST1', 'next_state': 'NONE', 'transition_time': '1308614400.0'" in endpoint1.to_str()
    assert "'prev_state': 'None', 'state': 'NONE', 'next_state': 'TEST2', 'transition_time': '1308614400.0'" in endpoint2.to_str()
    assert "'prev_state': 'None', 'state': 'TEST1', 'next_state': 'TEST2', 'transition_time': '1308614400.0'" in endpoint3.to_str()


def test_endpoint_state_default():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint1.update_state('UNKNOWN')
    endpoint1.update_state()

    assert endpoint1.state == 'UNKNOWN' and endpoint1.next_state == 'NONE'


def test_elapsed_time():
    time.time = mock_time
    endpoint1 = endPoint.EndPoint(test_data)
    e1 = endpoint1.elapsed_time(0)
    assert e1 == 1308614400.0
    e2 = endpoint1.elapsed_time()
    assert e2 == 0
