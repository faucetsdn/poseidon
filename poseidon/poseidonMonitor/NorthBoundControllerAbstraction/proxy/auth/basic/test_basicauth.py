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
Test module for basicauth.

@author: kylez
"""
import base64
import logging
import os

import pytest
from httmock import HTTMock
from httmock import response
from httmock import urlmatch

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.basic.basicauth import BasicAuthControllerProxy

module_logger = logging.getLogger(__name__)

cur_dir = os.path.dirname(os.path.realpath(__file__))
username = 'user'
password = 'pass'


def mock_factory(regex, filemap):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        if url.path not in filemap:  # pragma: no cover
            raise Exception('Invalid URL: %s' % url)
        user, pass_ = base64.b64decode(
            request.headers['Authorization'].split()[1]).split(':')
        assert user == username
        assert pass_ == password
        with open(os.path.join(cur_dir, filemap[url.path])) as f:
            data = f.read().replace('\n', '')
        r = response(content=data)
        return r
    return mock_fn


def test_BasicAuthControllerProxy():
    """
    Tests BasicAuthControllerProxy
    """
    filemap = {
        '/resource': 'sample_content.txt'
    }
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BasicAuthControllerProxy(
            'http://localhost/', auth=('user', 'pass'))
        res = proxy.get_resource('/resource')
        assert proxy
