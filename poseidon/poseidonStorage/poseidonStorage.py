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
Created on 17 May 2016
@author: dgrossman, lanhamt
"""
from pymongo import MongoClient
import ConfigParser
import os
import json
import socket


class poseidonStorage:
    """
    poseidonStorage class for managing mongodb database

    NOTE: currently assumes that poseidonStorage executes
    on same machine as mongo image is running on.
    """
    def __init__(self):
        self.modName = 'poseidonStorage'

        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open('/poseidonWork/templates/config.template'))
        database_ip = self.config.get('database', 'ip')
        self.client = MongoClient(database_ip)


class db_collection_names_test(poseidonStorage):
    """
    rest class to get names of collections in default
    database
    """
    def on_get(self, req, resp):
        try:
            ret = self.client.database.collection_names()
        except:
            ret = "Error on retrieving colleciton names."
        resp.body = json.dumps(ret)


class db_collection_test(poseidonStorage):
    """
    rest class to test document in collection
    """
    def on_get(self, req, resp, collection):
        try:
            ret = self.client[collection]
        except:
            ret = "Could not find collection: " + collection + " in database."
        resp.body = json.dumps(ret)


class db_query_id_test(poseidonStorage):
    """
    rest class to test query
    """
    def on_get(self, req, resp):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
