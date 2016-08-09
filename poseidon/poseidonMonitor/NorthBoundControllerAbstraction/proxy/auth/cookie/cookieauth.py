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

from urlparse import urljoin
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.controllerproxy import ControllerProxy


class CookieAuthControllerProxy(ControllerProxy):
    def __init__(self, base_uri, login_resource, auth, *args, **kwargs):
        super(CookieAuthControllerProxy, self).__init__(base_uri, *args, **kwargs)
        self.login_resource = login_resource
        self.auth = auth
        r = self.session.post(urljoin(self.base_uri, login_resource), json=auth, verify=False)
        self.session.cookies = r.cookies