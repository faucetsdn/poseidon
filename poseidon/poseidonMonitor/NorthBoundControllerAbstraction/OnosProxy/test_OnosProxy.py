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
Test module for OnosProxy.

@author: kylez
"""

import pytest
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.OnosProxy.OnosProxy import OnosProxy

import os
import json
from httmock import urlmatch, response, HTTMock

cur_dir = os.path.dirname(os.path.realpath(__file__))

def mock_factory(regex, file):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        with open(file) as f:
            data = f.read().replace('\n', '')
        content = json.dumps(json.loads(data))
        r = response(content=content)
        return r
    return mock_fn

def test_OnosProxy():
    """
    Tests OnosProxy
    """
    proxy = OnosProxy("base_uri", ("user", "pass"))
    assert proxy

def test_OnosProxy_get_devices():
    with HTTMock(mock_factory(r'.*', os.path.join(cur_dir, "devices.sample"))):
        proxy = OnosProxy("http://localhost/onos/v1/", auth=("user", "pass"))
        r = proxy.get_devices()

def test_OnosProxy_get_hosts():
    with HTTMock(mock_factory(r'.*', os.path.join(cur_dir, "hosts.sample"))):
        proxy = OnosProxy("http://localhost/onos/v1/", auth=("user", "pass"))
        r = proxy.get_hosts()

def test_OnosProxy_get_flows():
    with HTTMock(mock_factory(r'.*', os.path.join(cur_dir, "flows.sample"))):
        proxy = OnosProxy("http://localhost/onos/v1/", auth=("user", "pass"))
        r = proxy.get_flows()