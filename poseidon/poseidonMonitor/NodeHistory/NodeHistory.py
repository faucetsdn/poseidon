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
import json
import logging

from requests import get

from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base

module_logger = logging.getLogger(__name__)


class NodeHistory(Monitor_Action_Base):

    def __init__(self):
        super(NodeHistory, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__


class Handle_Default(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Default, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__

    @staticmethod
    def on_get(req, resp, resource):
        resp.content_type = 'application/json'
        try:
            """
            connect to poseidon storage to query database
            dump response from storage
            db_collection_query
            query = {'node_ip': resource}
            urllib.unquote(query).encode('utf8')

            """
            query = {'node_ip': resource}
            query = urllib.unquote(query).encode('utf8')
            response = get('http://localhost:4444/v1/storage/' + query)
        except:  # pragma: no cover
            response = 'failed'
        resp.body = json.dumps(response)


nodehistory_interface = NodeHistory()
nodehistory_interface.add_endpoint('Handle_Default', Handle_Default)
