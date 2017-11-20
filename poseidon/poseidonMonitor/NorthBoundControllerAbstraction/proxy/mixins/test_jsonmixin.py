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
Test module for jsonmixin.

@author: kylez
"""
import json
import os

from httmock import response

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.mixins.jsonmixin import JsonMixin

cur_dir = os.path.dirname(os.path.realpath(__file__))

moudle_logger = Logger.logger


def test_JsonMixin():
    """
    Tests JsonMixin
    """
    # Craft a JSON response object
    with open(os.path.join(cur_dir, 'sample_json.json')) as f:
        j = json.loads(f.read().replace('\n', ''))
    res = response(content=json.dumps(j), headers={
                   'content-type': 'application/json'})

    # Parse the JSON response object
    parsed = JsonMixin.parse_json(res)
    assert parsed


def test_empty():
    # Verify that blank text fields are parsed properly.
    def obj(): return True  # Just a proxy object for attaching text field.
    obj.text = ""

    # see if this forces coverge of obj
    assert obj()

    parsed = JsonMixin.parse_json(obj)
    assert parsed == {}
