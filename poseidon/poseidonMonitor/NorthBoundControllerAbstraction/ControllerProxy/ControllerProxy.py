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
Created on 11 July 2016
@author: kylez
"""

import requests
import json
from urlparse import urljoin

class ControllerProxy(object):
    def __init__(self, base_uri):
        self.base_uri = base_uri

    def get_resource(self, resource, auth=None):
        """
        GET a REST resource, using optional auth.

        NOTE: if `resource` starts with a slash (/), then it will be considered to be an absolute resource
        # urljoin("http://localhost/path/to/", "/resource")
        # will become "http://localhost/resource", and NOT "http://localhost/path/to/resource"
        """
        uri = urljoin(self.base_uri, resource)
        return requests.get(uri, auth=auth)

    def get_json_resource(self, resource, auth=None):
        """
        GET a REST resource using optional auth, then parse JSON from the `text` field.
        """
        r = self.get_resource(resource, auth=auth)
        j = json.loads(r.text)
        return j


