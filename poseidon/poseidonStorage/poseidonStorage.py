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
poseidonStorage interface for mongodb container
for persistent storage.

NAMES: current databases and collections (subject to change)

    db                      collection
    ---                     ---
    poseidon_records        network_graph

Created on 17 May 2016
@author: dgrossman, lanhamt
"""
import ast
import ConfigParser
import json
import urllib
import falcon
from subprocess import check_output
from pymongo import MongoClient
from falcon_cors import CORS
from os import environ


class poseidonStorage:
    """
    poseidonStorage class for managing mongodb database,
    brokers requests to database.

    NOTE: currently attempts to retrieve database ip from
    env variable named DOCKER_HOST, if absent tries to get
    from config file, else raises connection error.
    """

    def __init__(self):
        self.modName = 'poseidonStorage'

        database_container_ip = ''
        database_container_ip = check_output(
            "env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-",
            shell=True).strip()
        if not database_container_ip:
            # did not find env variable DOCKER_HOST
            try:
                self.config = ConfigParser.ConfigParser()
                self.config.readfp(
                    open('/poseidonWork/templates/config.template'))
                database_container_ip = self.config.get('database', 'ip')
            except:
                raise ValueError(
                    'poseidonStorage: could not find database ip address.')
        self.client = MongoClient(database_container_ip)

        # create db named 'poseidon_records' (NOTE: db will not actually be
        # created until first doc write).
        # db stores reference object for the database
        self.db = self.client.poseidon_records


def get_allowed():
    rest_url = 'localhost:28000'
    if 'ALLOW_ORIGIN' in environ:
        allow_origin = environ['ALLOW_ORIGIN']
        host_port = allow_origin.split('//')[1]
        host = host_port.split(':')[0]
        port = str(int(host_port.split(':')[1]))
        rest_url = host + ':' + port
    else:
        allow_origin = ''
    return allow_origin, rest_url

allow_origin, rest_url = get_allowed()
cors = CORS(allow_origins_list=[allow_origin])
public_cors = CORS(allow_all_origins=True)


class db_database_names(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    gets names of databases.
    """

    def on_get(self, req, resp):
        try:
            ret = self.client.database_names()
        except:
            ret = 'Error in connecting to mongo container'
        resp.body = json.dumps(ret)


class db_collection_names(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    get names of collections in given
    database.
    """

    def on_get(self, req, resp, database):
        ret = self.client[database].collection_names()
        # empty list returned for non-existent database
        if not ret:
            ret = 'Error on retrieving colleciton names.'
        resp.body = json.dumps(ret)


class db_collection_count(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    gets information for given collection.
    """

    def on_get(self, req, resp, database, collection):
        ret = self.client[database][collection].count()
        resp.body = json.dumps(ret)


class db_retrieve_doc(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    gets document in given database with given id.
    """

    def on_get(self, req, resp, database, collection, doc_id):
        ret = self.client[database][collection].find_one({'_id': doc_id})
        if not ret:
            ret = 'Error retrieving document with id: ' + doc_id + '.'
        resp.body = json.dumps(ret)


class db_collection_query(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    queries given database and collection,
    returns documents found in query.

    NOTE: supports utf8 url encoding for well-formed
    queries (ie "{u'author': u'some author'}")
    """

    def on_get(self, req, resp, database, collection, query_str):
        try:
            query = urllib.unquote(query_str).decode('utf8')
            query = ast.literal_eval(query_str)
            cursor = self.client[database][collection].find(query)
            ret = ''
            for doc in cursor:
                ret += json.dumps(doc)
            if not ret:
                ret = json.dumps('Valid query performed: no documents found.')
        except:
            ret = json.dumps('Error on query.')
        resp.body = ret


class db_add_one_doc(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    adds a document to specified database and
    collection. returned response includes
    the id of the newly inserted object.

    NOTE: uses utf8 decoding for document
    to be inserted into database.
    """

    def on_get(self, req, resp, database, collection, doc):
        try:
            doc = urllib.unquote(doc).decode('utf8')
            doc = ast.literal_eval(doc)
            ret = self.client[database][collection].insert_one(doc)
            ret = str(ret.inserted_id)
        except:
            ret = 'Error inserting document into database.'
        resp.body = json.dumps(ret)


class db_add_many_docs(poseidonStorage):
    """
    rest layer subclass of poseidonStorage.
    adds a list of documents (encoded with
    utf8) to specified database and collection.
    returned response includes the list of ids
    for the documents that have been inserted on
    success and error on failure.

    NOTE: uses utf8 decoding for documents to be
    inserted.
    """

    def on_get(self, req, resp, database, collection, doc_list):
        try:
            doc_list = urllib.unquote(doc_list).decode('utf8')
            doc_list = ast.literal_eval(doc_list)
            ret = self.client[database][collection].insert_many(doc_list)
            for o_id in ret:
                o_id = str(o_id.inserted_id)
        except:
            ret = 'Error inserting documents into database.'
        resp.body = json.dumps(ret)


# create callable WSGI app instance for gunicorn
api = falcon.API(middleware=[cors.middleware])

# add local routes for db api
api.add_route('/v1/storage', db_database_names())
api.add_route('/v1/storage/{database}', db_collection_names())
api.add_route(
    '/v1/storage/{database}/{collection}',
    db_collection_count())
api.add_route(
    '/v1/storage/doc/{database}/{collection}/{doc_id}',
    db_retrieve_doc())
api.add_route(
    '/v1/storage/query/{database}/{collection}/{query_str}',
    db_collection_query())
api.add_route(
    '/v1/storage/add_one_doc/{database}/{collection}/{doc_str}',
    db_add_one_doc())
api.add_route(
    '/v1/storage/add_many_docs/{database}/{collection}/{doc_list}',
    db_add_many_docs())


def main():
    """
    Initialization to run in mongo container -
    pull desired database options from config.
    """
    pass


if __name__ == '__main__':
    main()
