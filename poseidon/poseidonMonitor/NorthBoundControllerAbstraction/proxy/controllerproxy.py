#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
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
Created on 25 July 2016

@author: kylez
"""
import requests
from urllib.parse import urljoin

from poseidon.baseClasses.Logger_Base import Logger

module_logger = Logger
requests.packages.urllib3.disable_warnings()


class ControllerProxy(object):

    def __init__(self, base_uri, *args, **kwargs):
        self.logger = module_logger.logger
        self.poseidon_logger = module_logger.poseidon_logger
        self.base_uri = base_uri
        self.session = requests.Session()

    def get_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.session.get(uri, *args, **kwargs)

    def post_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.session.post(uri, *args, **kwargs)

    def request_resource(self, *args, **kwargs):
        return self.session.request(*args, **kwargs)
