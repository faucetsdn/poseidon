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
Test module for ControllerPolling.py

Created on 5 July 2016
@author: dgrossman
"""
import falcon
import pytest
from ControllerPolling import ControllerPolling

application = falcon.API()
application.add_route('/v1/Polling', ControllerPolling())


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_p2c(client):
    """
    Tests ControllerPolling
    """
    resp = client.get('/v1/Polling')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'application/json':
            resp_type = r_type
    assert resp_type == 'application/json'
