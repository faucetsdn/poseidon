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
