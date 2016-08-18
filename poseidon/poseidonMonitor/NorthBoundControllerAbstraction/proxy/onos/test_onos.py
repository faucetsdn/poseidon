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
Test module for onos.

@author: kylez
"""
import json
import logging
import os

import pytest
from httmock import HTTMock
from httmock import response
from httmock import urlmatch
from onos import OnosProxy


module_logger = logging.getLogger('poseidonMonitor.NBCA.proxy.onos.test_onos')
cur_dir = os.path.dirname(os.path.realpath(__file__))
username = 'user'
password = 'pass'


def mock_factory(regex, filemap):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        if url.path not in filemap:  # pragma: no cover
            raise Exception('Invalid URL: %s' % url)
        with open(os.path.join(cur_dir, filemap[url.path])) as f:
            data = f.read().replace('\n', '')
        content = json.dumps(json.loads(data))
        r = response(content=content)
        return r
    return mock_fn


def test_OnosProxy():
    """
    Tests onos
    """
    filemap = {
        '/devices': 'sample_devices.json',
        '/hosts': 'hosts.sample',
        '/flows': 'flows.sample'
    }
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = OnosProxy('http://localhost', ('user', 'pass'))
        assert proxy
        devices = proxy.get_devices()
        assert devices
        hosts = proxy.get_hosts()
        assert hosts
        flows = proxy.get_flows()
        assert flows
