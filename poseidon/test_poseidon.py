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

Created on 17 May 2016
@author: Charlie Lewis
"""

from poseidon import QuoteResource

import falcon
import json
import pytest

application = falcon.API()
application.add_route('/quote', QuoteResource())

# exposes the application for testing
@pytest.fixture
def app():
    return application

def test_quote_resource_get(client):
    """
    Tests the on_get function of the QuoteResource class.
    """
    resp = client.get('/quote')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'application/json':
            resp_type = r_type
    assert resp_type == 'application/json'
    assert resp.json['author'] == 'Grace Hopper'
    assert resp.json['quote'] == 'I\'ve always been more interested in the future than in the past.'
