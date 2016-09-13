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
import os
import bson
import falcon
import pytest
import json
from poseidonStorage import get_allowed
from poseidonStorage import db_add_many_docs
from poseidonStorage import db_add_one_doc
from poseidonStorage import db_collection_count
from poseidonStorage import db_collection_names
from poseidonStorage import db_collection_query
from poseidonStorage import db_database_names
from poseidonStorage import db_retrieve_doc
from poseidonStorage import db_update_one_doc
from poseidonStorage import main
from poseidonStorage import poseidonStorage


application = falcon.API()
application.add_route(
    '/v1/storage',
    db_database_names())
application.add_route(
    '/v1/storage/{database}',
    db_collection_names())
application.add_route(
    '/v1/storage/{database}/{collection}',
    db_collection_count())
application.add_route(
    '/v1/storage/doc/{database}/{collection}/{doc_id}',
    db_retrieve_doc())
application.add_route(
    '/v1/storage/query/{database}/{collection}/{query_str}',
    db_collection_query())
application.add_route(
    '/v1/storage/add_one_doc/{database}/{collection}',
    db_add_one_doc())
application.add_route(
    '/v1/storage/add_many_docs/{database}/{collection}',
    db_add_many_docs())
application.add_route(
    '/v1/storage/update_one_doc/{database}/{collection}/{filt}',
    db_update_one_doc())


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


def test_get_allowed():
    get_allowed()
    os.environ['ALLOW_ORIGIN'] = 'tcp://1.1.1.1:1234'
    get_allowed()


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
    names = json.loads(resp.body)
    assert names == []


def test_db_collection_count(client):
    """
    tests retrieval of document count for
    a given database and collection.
    """
    resp = client.get('/v1/storage/local/startup_log')
    assert resp.status == falcon.HTTP_OK
    assert int(resp.body) >= 1


def test_db_retrieve_doc(client):
    """
    tests retrieval of document from a
    given database and collection.
    If no document is found then error message
    is returned.
    """
    resp = client.get(
        '/v1/storage/doc/local/startup_log/ffffffffffffffffffffffff')
    assert resp.status == falcon.HTTP_OK

    resp = client.get('/v1/storage/doc/local/startup_log/bad_id')
    assert resp.status == falcon.HTTP_BAD_REQUEST
    assert resp.body == '"Bad document id."'


def test_db_collection_query(client):
    """
    tests response from query of database.
    response is a serialized dict with 'count'
    and 'docs' fields.
    """
    query = {}
    query = json.dumps(query)
    resp = client.get('/v1/storage/query/' + 'local/' + 'startup_log/' + query)
    assert resp.status == falcon.HTTP_OK
    resp = json.loads(resp.body)
    assert resp['count'] >= 0

    query = 'bad'
    resp = client.get('/v1/storage/query/' + 'local/' + 'startup_log/' + query)
    assert resp.status == falcon.HTTP_BAD_REQUEST
    resp = json.loads(resp.body)
    assert resp['count'] == -1


def test_db_add_one_doc(client):
    """
    tests adding document to a database, then
    tests retrieving added document from the database
    using the returned id, then tests that the collection
    inserted into is listed under the database collections.
    """
    doc = {}
    doc['node_ip'] = 'TEST'
    doc['talked_to'] = {'machine_1': 2,
                        'machine_2': 1,
                        'machine_3': 1}
    doc['recieved_from'] = {'machine_1': 1,
                            'machine_6': 3,
                            'machine_2': 2}
    doc['packet_lengths'] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    doc['flow_id'] = '6a32984d2348e23894f3298'
    doc['dns_records'] = ['0.0.0.0', '1.1.1.1']
    doc['time_rec'] = {'first_sent': '0-0-0 00:00:00.000000',
                       'first_received': '0-0-0 00:00:00.000000',
                       'last_sent': '0-0-0 00:00:00.000000',
                       'last_received': '0-0-0 00:00:00.000000'}
    # adds doc to db
    uri = '/v1/storage/add_one_doc/' + 'test_poseidon_records/' + 'network_graph'
    resp = client.post(uri, data=json.dumps(doc))
    assert resp.status == falcon.HTTP_OK
    doc_id = json.loads(resp.body)

    # retrieves doc from db
    uri = '/v1/storage/doc/' + 'test_poseidon_records/' + 'network_graph/' + doc_id
    resp = client.get(uri)
    assert resp.status == falcon.HTTP_OK
    doc = json.loads(resp.body)
    assert doc['node_ip'] == 'TEST'
    assert doc['packet_lengths'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # checks that collection is persistent
    resp = client.get('/v1/storage/' + 'test_poseidon_records')
    assert resp.status == falcon.HTTP_OK
    assert 'network_graph' in json.loads(resp.body)

    # checks that number of documents in collection at least one now
    resp = client.get('/v1/storage/' + 'test_poseidon_records/' + 'network_graph')
    assert int(resp.body) >= 1

    # test a query of the inserted collection with a bad object id
    query = {'_id': 'xyz'}
    query = json.dumps(query)
    resp = client.get('/v1/storage/query/' + 'test_poseidon_records/' + 'network_graph/' + query)
    assert resp.status == falcon.HTTP_BAD_REQUEST

    # test a proper query of the collection for the inserted doc by id
    query = {'_id': doc_id}
    query = json.dumps(query)
    resp = client.get('/v1/storage/query/' + 'test_poseidon_records/' + 'network_graph/' + query)
    assert resp.status == falcon.HTTP_OK
    resp = json.loads(resp.body)
    assert resp['count'] >= 1

    # test a collection query using the node_ip
    query = {'node_ip': 'TEST'}
    query = json.dumps(query)
    resp = client.get('/v1/storage/query/' + 'test_poseidon_records/' + 'network_graph/' + query)
    assert resp.status == falcon.HTTP_OK
    resp = json.loads(resp.body)
    assert resp['count'] >= 1
    doc = resp['docs'][0]  # should only have 1 doc in list
    assert doc['node_ip'] == 'TEST'
    assert doc['flow_id'] == '6a32984d2348e23894f3298'


def test_db_add_many_docs(client):
    """
    tests inserting several docs into database.
    encodes with bson for well-formatted url.
    """
    doc_one = {}
    doc_one['node_ip'] = '1.1.1.1'
    doc_one['packet_lengths'] = [1, 1, 2]

    doc_two = {}
    doc_two['node_ip'] = '2.2.2.2'
    doc_two['packet_lengths'] = [3, 5, 8]

    doc_thr = {}
    doc_thr['node_ip'] = '3.3.3.3'
    doc_thr['packet_lengths'] = [13, 21, 34]

    # insert 3 docs
    docs = [doc_one, doc_two, doc_thr]
    uri = '/v1/storage/add_many_docs/'+'test_poseidon_records/'+'network_graph/'
    resp = client.post(uri, data=json.dumps(docs))
    assert resp.status == falcon.HTTP_OK
    resp = json.loads(resp.body)
    assert len(resp) == 3

    # check that inserted docs are in collection
    query = {}
    query = json.dumps(query)
    resp = client.get('/v1/storage/query/' + 'test_poseidon_records/' + 'network_graph/' + query)
    assert resp.status == falcon.HTTP_OK
    resp = json.loads(resp.body)
    assert resp['count'] >= 3


def test_db_update_one_doc(client):
    """
    tests updating nonexistent doc,
    encodes filter and updated doc with
    bson.
    """
    filt = {'node_ip': '-1.-1.-1.-1'}
    update = {'node_ip': '-1.-1.-1.-1', 'new_field': 101}

    # non-existent document
    filt = json.dumps(filt)
    uri = '/v1/storage/update_one_doc/'+'test_poseidon_records/'+'network_graph/'+filt
    resp = client.post(uri, data=json.dumps(update))
    assert resp.status == falcon.HTTP_BAD_REQUEST
    resp = json.loads(resp.body)
    assert not resp['success']

    # insert doc
    doc = {'node_ip': 'GIRAFFE'}
    uri = '/v1/storage/add_one_doc/' + 'test_poseidon_records/' + 'network_graph'
    resp = client.post(uri, data=json.dumps(doc))
    assert resp.status == falcon.HTTP_OK

    # update doc node_ip
    doc_id = json.loads(resp.body)
    filt = {'_id': doc_id}
    filt = json.dumps(filt)
    update = {'$set': {'node_ip': 'HIPPO'}}
    uri = '/v1/storage/update_one_doc/'+'test_poseidon_records/'+'network_graph/'+filt
    resp = client.post(uri, data=json.dumps(update))
    assert resp.status == falcon.HTTP_OK
    assert json.loads(resp.body)['raw_result']['updatedExisting']

    # verify update to node_ip
    uri = '/v1/storage/doc/' + 'test_poseidon_records/' + 'network_graph/' + doc_id
    resp = client.get(uri)
    assert resp.status == falcon.HTTP_OK
    doc = json.loads(resp.body)
    assert doc['node_ip'] == 'HIPPO'
