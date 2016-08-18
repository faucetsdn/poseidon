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
Created on 25 July 2016

@author: kylez
"""
import logging
from urlparse import urljoin

import requests

module_logger = logging.getLogger('poseidonMonitor.NBCA.proxy/controllerproxy')


class ControllerProxy(object):

    def __init__(self, base_uri, *args, **kwargs):
        self.logger = module_logger
        self.base_uri = base_uri
        self.session = requests.Session()

    def get_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.session.get(uri, *args, **kwargs)
