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
Test module for Config.py

Created on 28 June 2016
@author: dgrossman, lanhamt
"""
import logging

import falcon
import pytest
from Config import config_interface

module_logger = logging.getLogger(__name__)

application = falcon.API()
application.add_route('/v1/config',
                      config_interface.get_endpoint('Handle_FullConfig'))
application.add_route('/v1/config/{section}',
                      config_interface.get_endpoint('Handle_SectionConfig'))
application.add_route('/v1/config/{section}/{field}',
                      config_interface.get_endpoint('Handle_FieldConfig'))


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_config_full_get(client):
    """
    Tests retrieving the entire config file.
    """
    resp = client.get('/v1/config')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'application/json':
            resp_type = r_type
    assert resp_type == 'application/json'


def test_config_section_get_OK(client):
    """
    Tests retrieving a section in the config file.
    """
    resp = client.get('/v1/config/rest config test')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '[["key1", "trident"], ["key2", "theseus"], ["double key", "atlas horses"]]'


def test_config_section_get_FAIL(client):
    resp = client.get('/v1/config/not_a_section')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '"Failed to find section: not_a_section"'


def test_config_field_get_1(client):
    """
    Tests retrieving field from a section in the config file.
    """
    resp = client.get('/v1/config/rest config test/key1')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'trident'


def test_config_field_get_2(client):
    resp = client.get('/v1/config/rest config test/key2')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'theseus'


def test_config_field_get_3T(client):
    resp = client.get('/v1/config/rest config test/double key')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'atlas horses'


def test_config_field_get_4F(client):
    resp = client.get('/v1/config/bad_section/not_a_key')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == 'Can\'t find field: not_a_key in section: bad_section'
