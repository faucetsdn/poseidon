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
Test module for poseidonStorage

Created on 28 June 2016
@author: dgrossman, lanhamt
"""
import pytest
import falcon
from poseidonStorage import poseidonStorage
from poseidonStorage import db_collection_test
from poseidonStorage import db_document_test
from poseidonStorage import db_query_id_test


application = falcon.API()
application.add_route('/v1/storage/{collection}', db_collection_test)
application.add_route('/v1/storage/{database}/{collection}', db_document_test)
application.add_route('/v1/storage/query/{query}', db_query_id_test)


def test_poseidonStorage():
    ps = poseidonStorage()
    # assert ps.client.address == ('localhost', 27017)


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_db_collection_get(client):
    resp = client.get('/v1/storage/local')


def test_db_document_get(client):
    resp = client.get('/v1/storage/local/startup_log')


def test_db_query_id_get(client):
    resp = client.get('/v1/storage/query/not_a_query')
