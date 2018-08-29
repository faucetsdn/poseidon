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
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from poseidon.baseClasses.Logger_Base import Logger

requests.packages.urllib3.disable_warnings()


class ControllerProxy(object):

    def __init__(self, base_uri, *args, **kwargs):
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.base_uri = base_uri
        self.session = requests.Session()

    @staticmethod
    def requests_retry_session(retries=3,
                               backoff_factor=0.3,
                               status_forcelist=(500,502,504),
                               session=None,):
        session = session or requests.Session()
        retry = Retry(total=retries,
                      read=retries,
                      connect=0,
                      backoff_factor=backoff_factor,
                      status_forcelist=status_forcelist,)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def get_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.requests_retry_session(session=self.session).get(uri, timeout=(1, 10), *args, **kwargs)

    def post_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.requests_retry_session(session=self.session).post(uri, timeout=(1, 10), *args, **kwargs)

    def request_resource(self, *args, **kwargs):
        return self.requests_retry_session(session=self.session).request(timeout=(1, 10), *args, **kwargs)
