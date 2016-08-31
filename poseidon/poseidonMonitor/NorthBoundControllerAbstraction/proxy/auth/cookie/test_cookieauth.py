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
Test module for cookieauth.

@author: kylez
"""
import json
import logging
import os

import pytest
from httmock import HTTMock
from httmock import response
from httmock import urlmatch

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.cookie.cookieauth import CookieAuthControllerProxy

module_logger = logging.getLogger(__name__)

cur_dir = os.path.dirname(os.path.realpath(__file__))
username = 'user'
password = 'pass'
cookie = 'cookie'


def mock_factory(regex, filemap):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        if url.path == '/login':
            j = json.loads(request.body)
            assert j['username'] == username
            assert j['password'] == password
            headers = {'set-cookie': 'session_cookie={0}'.format(cookie)}
            r = response(headers=headers, request=request)
        elif url.path in filemap:
            with open(os.path.join(cur_dir, filemap[url.path])) as f:
                data = f.read().replace('\n', '')
            r = response(content=data, request=request)
        else:  # pragma: no cover
            raise Exception('Invalid URL: {0}'.format(url))
        return r
    return mock_fn


def test_CookieAuthControllerProxy():
    """
    Tests CookieAuthControllerProxy
    """
    filemap = {
        '/resource': 'sample_content.txt'
    }

    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = CookieAuthControllerProxy(
            base_uri='http://localhost', login_resource='login', auth={'username': username, 'password': password})
        res = proxy.get_resource('resource')
        assert res
