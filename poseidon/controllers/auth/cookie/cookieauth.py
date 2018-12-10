# -*- coding: utf-8 -*-
"""
Created on 25 July 2016
@author: kylez
"""
from urllib.parse import urljoin

from poseidon.controllers.controllerproxy import ControllerProxy
from poseidon.helpers.log import Logger


class CookieAuthControllerProxy(ControllerProxy):

    def __init__(self, base_uri, login_resource, auth, *args, **kwargs):
        super(CookieAuthControllerProxy, self).__init__(
            base_uri, *args, **kwargs)
        self.login_resource = login_resource
        self.auth = auth
        r = ControllerProxy.requests_retry_session(session=self.session).post(
            urljoin(self.base_uri, login_resource), timeout=(1, 10), json=auth, verify=False)
        self.session.cookies = r.cookies
