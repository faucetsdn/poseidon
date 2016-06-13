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
Test module for poseidon.py

Created on 13 June 2016
@author: Charlie Lewis
"""

import pytest

from tcpdump_hex_parser import get_path
from tcpdump_hex_parser import run_tool

def test_get_path():
    get_path()

def test_run_tool():
    with open('/tmp/test', 'w') as f:
        f.write("this is a test file")
    run_tool('/tmp/test')
