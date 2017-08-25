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
Test module for NorthBoundControllerAbstraction.py

Created on 28 June 2016
@author: dgrossman
"""
import logging

import falcon
import pytest

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import controller_interface

module_logger = logging.getLogger(__name__)


application = falcon.API()
application.add_route(
    '/v1/Nbca/resource/{resource}',
    controller_interface.get_endpoint('Handle_Resource'))
application.add_route(
    '/v1/Nbca/periodic',
    controller_interface.get_endpoint('Handle_Periodic'))


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_NorthBoundControllerAbstraction(client):
    """
    Tests the NorthBoundControllerAbstraction
    Handle_Resource class
    """
    resp = client.get('/v1/Nbca/resource/someNbcaRequest')
    assert resp.status == falcon.HTTP_OK


def test_NorthBoundControllerAbstraction_periodic(client):
    #    """
    #    Tests NorthBoundControllerAbstraction Handle_Periodic
    #    class.
    #    """
    #    resp = client.get('/v1/Nbca/periodic')
    #    assert resp.status == falcon.HTTP_OK
    #    package = ast.literal_eval(resp.body)
    #    assert isinstance(package['times'], int)
    #    assert 'controller' in package
    #    assert 'service' in package
    #    if 'establish' in package['controller']:
    #        assert 'Could not' in package['controller']
    #    else:
    #        assert int(package['controller']) <= 10
    #        assert int(package['controller']) >= 1
    pass
