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
Test module for PoseidonNbca.py

Created on 28 June 2016
@author: dgrossman
"""
import falcon
import pytest
from PoseidonNbca import PoseidonNbca

application = falcon.API()
application.add_route('/v1/Nbca/{resource}', PoseidonNbca())


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_PoseidonNbca(client):
    """
    Tests the PoseidonHisotry class
    """
    resp = client.get('/v1/Nbca/someNbcaRequest')
    assert resp.status == falcon.HTTP_OK
