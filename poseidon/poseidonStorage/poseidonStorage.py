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
PoseidonStorage interface for mongodb container
for persistent storage.

NAMES: current databases and collections (subject to change)

    db                      collection
    ---                     ---
    poseidon_records        network_graph
                            models

Created on 17 May 2016
@author: dgrossman, lanhamt
"""
import ConfigParser
import json
import sys
import bson
import falcon
from falcon_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from os import environ
from subprocess import check_output
from urlparse import urlparse


class MongoJSONEncoder(json.JSONEncoder):
    """
    JSON encoder to handle special case
    ObjectId objects and datetime objects
    for serialization.
    """
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


# exceptions for malformed bson
bsonInputExceptions = (bson.errors.BSONError,
                       bson.errors.InvalidId,
                       bson.errors.InvalidStringData,
                       bson.errors.InvalidDocument,
                       bson.errors.InvalidBSON)


class PoseidonStorage(object):
    """
    PoseidonStorage class for managing mongodb database,
    brokers requests to database.

    NOTE: retrieves database host from config
    file in config/poseidon.config under the
    [PoseidonMain] section.
    """

    def __init__(self):
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.readfp(
                open('/poseidonWork/config/poseidon.config'))
            section_name = 'PoseidonStorage'
            field_name = 'database'
            database_container_ip = self.config.get(section_name, field_name)
        except:  # pragma: no cover
            raise ValueError(
                'PoseidonStorage: could not find database ip address.')
        self.client = MongoClient(host=database_container_ip)


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
cors = CORS(allow_all_origins=True)
public_cors = CORS(allow_all_origins=True)


class db_database_names(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/
        Method:     GET
    Response:
        Body:       json encoded list of db names
    """

    def on_get(self, req, resp):
        try:
            ret = self.client.database_names()
        except:  # pragma: no cover
            ret = 'Error in connecting to mongo container'
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_collection_names(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/{database}
        Method:     GET
    Response:
        Body:       json encoded list of collection
                    names for given db
    """

    def on_get(self, req, resp, database):
        try:
            ret = self.client[database].collection_names()
        except:  # pragma: no cover
            ret = 'Error on retrieving colleciton names.'
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_collection_count(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/{database}/{collection}
        Method:     GET
    Response:
        Body:       json encoded (string) number of
                    documents in given collection
    """

    def on_get(self, req, resp, database, collection):
        try:
            ret = self.client[database][collection].count()
        except:  # pragma: no cover
            ret = 'Error retrieving collection doc count.'
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_retrieve_doc(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/doc/{database}/{collection}/{doc_id}
        Method:     GET
        Attributes: doc_id is the string of the document's _id which
                    will be used to create an ObjectId to search the db.
    Response:
        Body:       json encoded document (mapping object), ObjectId
                    returned in doc in string form
    """

    def on_get(self, req, resp, database, collection, doc_id):
        try:
            obj = ObjectId(doc_id)
            ret = self.client[database][collection].find_one({'_id': obj})
        except bsonInputExceptions:
            ret = 'Bad document id.'
            resp.status = falcon.HTTP_BAD_REQUEST
        except:  # pragma: no cover
            ret = 'Error retrieving document with id: ' + doc_id + '.'
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_collection_query(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/query/{database}/{collection}/{query_str}
        Method:     GET
        Attributes: query_str should be a serialized string of a
                    mapping object - json encoded
    Response:
        Body:       json encoded dict with 'count' of docs
                    matching the query and 'docs' list of
                    documents matching the query; 'count' is
                    set to -1 on error
    """

    def on_get(self, req, resp, database, collection, query_str):
        ret = {}
        try:
            query = json.loads(query_str)
            if '_id' in query:
                query['_id'] = ObjectId(query['_id'])

            cursor = self.client[database][collection].find(query)
            if cursor.count() == 0:
                ret['count'] = cursor.count()
            else:
                doc_list = []
                for doc in cursor:
                    doc_list.append(doc)
                ret['docs'] = doc_list
                ret['count'] = cursor.count()
        except bsonInputExceptions, e:  # pragma: no cover
            ret['count'] = -1
            ret['error'] = str(e)
            resp.status = falcon.HTTP_BAD_REQUEST
        except (TypeError, ValueError), e:  # pragma: no cover
            # bad query string
            ret['count'] = -1
            ret['error'] = str(e)
            resp.status = falcon.HTTP_BAD_REQUEST
        except Exception, e:  # pragma: no cover
            ret['count'] = -1
            ret['error'] = str(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_add_one_doc(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/add_one_doc/{database}/{collection}
        Method:     POST
        Attributes: request body is json serialized string of mapping
                    object
    Response:
        Body:       string id of inserted document
    """

    def on_post(self, req, resp, database, collection):
        try:
            data = req.stream.read()
            data_dict = json.loads(data)
            ret = self.client[database][collection].insert_one(data_dict)
            ret = ret.inserted_id
        except Exception, e:  # pragma: no cover
            ret = str(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_add_many_docs(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/add_many_docs/{database}/{collection}
        Method:     POST
        Attributes: json encoded list of documents to be inserted
    Response:
        Body:       json encoded list of object ids (string form)
                    of inserted docs
    """

    def on_post(self, req, resp, database, collection):
        try:
            doc_list = req.stream.read()
            doc_list = json.loads(doc_list)
            result = self.client[database][collection].insert_many(doc_list)
            ret = []
            for obj_id in result.inserted_ids:
                ret.append(obj_id)
        except Exception, e:  # pragma: no cover
            ret = str(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


class db_update_one_doc(PoseidonStorage):
    """
    Request:
        URL:        /v1/storage/update_one_doc/{database}/{collection}/{filt}
        Method:     POST
        Attributes: json encoded document to replace existing, json encoded
                    filter
                    more info from mongodb:
                        https://docs.mongodb.com/getting-started/python/update/
                        https://docs.mongodb.com/manual/reference/operator/update/
    Response:
        Body:       dict with 'success' key indicating success or failure on
                    updating doc, and if successful the raw_result document
                    returned by the server
    """

    def on_post(self, req, resp, database, collection, filt):
        ret = {}
        try:
            doc_update = req.stream.read()
            doc_update = json.loads(doc_update)
            filt = json.loads(filt)
            if '_id' in filt:
                filt['_id'] = ObjectId(filt['_id'])
            result = self.client[database][collection].update_one(filt, doc_update)
            if result.modified_count == 1:
                ret['success'] = 1
                ret['raw_result'] = result.raw_result
            else:
                ret['success'] = 0
        except bsonInputExceptions:  # pragma: no cover
            ret['success'] = 0
            resp.status = falcon.HTTP_BAD_REQUEST
        except ValueError, TypeError:
            ret['success'] = 0
            resp.status = falcon.HTTP_BAD_REQUEST
        except Exception, e:  # pragma: no cover
            ret['success'] = 0
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
        resp.body = MongoJSONEncoder().encode(ret)


# create callable WSGI app instance for gunicorn
api = falcon.API(middleware=[cors.middleware])


# add local routes for db api
api.add_route(
    '/v1/storage',
    db_database_names())
api.add_route(
    '/v1/storage/{database}',
    db_collection_names())
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
    '/v1/storage/add_one_doc/{database}/{collection}',
    db_add_one_doc())
api.add_route(
    '/v1/storage/add_many_docs/{database}/{collection}',
    db_add_many_docs())
api.add_route(
    '/v1/storage/update_one_doc/{database}/{collection}/{filt}',
    db_update_one_doc())


def main():
    """
    Initialization to run in mongo container -
    pull desired database options from config.
    """
    pass


if __name__ == '__main__':
    main()
