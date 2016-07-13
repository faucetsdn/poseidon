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
Test module for poseidonStorage.
NOTE: responses are returned as json

Created on 28 June 2016
@author: dgrossman, lanhamt
"""
import pytest
import falcon
import urllib
from poseidonStorage import poseidonStorage
from poseidonStorage import main
from poseidonStorage import db_database_names
from poseidonStorage import db_collection_names
from poseidonStorage import db_collection_count
from poseidonStorage import db_retrieve_doc
from poseidonStorage import db_collection_query


application = falcon.API()
application.add_route('/v1/storage', db_database_names())
application.add_route('/v1/storage/{database}', db_collection_names())
application.add_route('/v1/storage/{database}/{collection}', db_collection_count())
application.add_route('/v1/storage/doc/{database}/{collection}/{doc_id}', db_retrieve_doc())
application.add_route('/v1/storage/query/{database}/{collection}/{query_str}', db_collection_query())


def test_poseidonStorage():
    """
    test of poseidonStorage class that
    brokers communication with the mongodb container.
    client.address tests connection to database and returns
    tuple of host and port. default port for mongodb
    is 27017.
    """
    ps = poseidonStorage()
    assert isinstance(ps.client.address, type(()))
    assert ps.client.PORT == 27017


def test_main():
    """
    tests main for poseidonStorage.
    """
    main()


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_db_database_names(client):
    """
    tests retrieval of database names from
    poseidonStorage.
    """
    resp = client.get('/v1/storage')
    assert resp.status == falcon.HTTP_OK
    assert 'local' in resp.body


def test_db_collection_names(client):
    """
    tests retrieval of collection names for a
    given database.
    """
    resp = client.get('/v1/storage/local')
    assert resp.status == falcon.HTTP_OK
    assert 'startup_log' in resp.body

    resp = client.get('/v1/storage/not_a_db')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '"Error on retrieving colleciton names."'


def test_db_collection_count(client):
    """
    tests retrieval of document count for
    a given database and collection.
    """
    resp = client.get('/v1/storage/local/startup_log')
    assert resp.status == falcon.HTTP_OK
    assert '1' in resp.body


def test_db_retrieve_doc(client):
    """
    tests retrieval of document from a
    given database and collection.
    If no document is found then error message
    is returned.
    """
    resp = client.get('/v1/storage/doc/local/startup_log/ffffffffffffffffffffffff')
    assert resp.status == falcon.HTTP_OK

    resp = client.get('/v1/storage/doc/local/startup_log/bad_id')
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '"Error retrieving document with id: bad_id."'


def test_db_collection_query(client):
    """
    tests response from query of database.
    """
    query = "{u'hostname': u'bad'}"
    query = urllib.unquote(query).encode('utf8')
    resp = client.get("/v1/storage/query/local/startup_log/" + query)
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '"Valid query performed: no documents found."'

    query = 'bad'
    resp = client.get("/v1/storage/query/local/startup_log/" + query)
    assert resp.status == falcon.HTTP_OK
    assert resp.body == '"Error on query."'
