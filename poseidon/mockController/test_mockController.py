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
test module for mock controller

Created on 14 July 2016
@author: lanhamt
"""
import falcon
import pytest
from mockController import MockController


application = falcon.API()
application.add_route('/v1/mock_controller/poll', MockController())


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_controller(client):
    """
    Tests mock controller get response, response
    should be json of rand int from 1 to 10.
    """
    resp = client.get('/v1/mock_controller/poll')
    assert resp.status == falcon.HTTP_OK
    num = int(resp.body)
    assert num >= 1 and num <= 10
