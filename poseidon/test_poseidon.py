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

import falcon
import json
import poseidon
import pytest

from os import environ
from poseidon import QuoteResource
from poseidon import SwaggerAPI
from poseidon import VersionResource

application = falcon.API()
application.add_route('/v1/quote', QuoteResource())
application.add_route('/swagger.yaml', SwaggerAPI())
application.add_route('/v1/version', VersionResource())

# exposes the application for testing
@pytest.fixture
def app():
    return application

def test_get_allowed():
    environ['ALLOW_ORIGIN'] = "http://test:80"
    allow_origin, rest_url = poseidon.get_allowed()

def test_swagger_api_get(client):
    """
    Tests the on_get function of the SwaggerAPI class.
    """
    resp = client.get('/swagger.yaml')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'text/yaml':
            resp_type = r_type
    assert resp_type == 'text/yaml'
    body = resp.body
    lines = body.split("\n")
    version = 'x'
    with open('VERSION', 'r') as f:
        version = f.read()
    body_version = 'y'
    for line in lines:
        if line.startswith("  version: "):
            body_version = line.split("  version: ")[1]
    assert version.strip() == body_version.strip()

def test_quote_resource_get(client):
    """
    Tests the on_get function of the QuoteResource class.
    """
    resp = client.get('/v1/quote')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'application/json':
            resp_type = r_type
    assert resp_type == 'application/json'
    assert resp.json['author'] == 'Grace Hopper'
    assert resp.json['quote'] == 'I\'ve always been more interested in the future than in the past.'

def test_version_resource_get(client):
    """
    Tests the on_get function of the VersionResource class.
    """
    resp = client.get('/v1/version')
    assert resp.status == falcon.HTTP_OK
    resp_type = None
    resp_types = resp.headers['Content-Type'].split(';')
    for r_type in resp_types:
        if r_type.strip() == 'application/json':
            resp_type = r_type
    assert resp_type == 'application/json'
    version = ''
    with open('VERSION', 'r') as f:
        version = f.read()
    assert version.strip() == resp.json['version']
