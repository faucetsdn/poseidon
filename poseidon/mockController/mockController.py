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
mock controller for testing

Created on 14 July 2016
@author: lanhamt
"""
import json
import random
from os import environ

import falcon
from falcon_cors import CORS


def get_allowed():
    rest_url = 'localhost:8555'
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


class MockController:
    """
    On get, returns random integer from
    1 to 10.
    """

    @staticmethod
    def on_get(req, resp):
        resp.body = json.dumps(random.randint(1, 10))


api = falcon.API(middleware=[cors.middleware])
api.add_route('/v1/mock_controller/poll', MockController())
