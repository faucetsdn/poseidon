# -*- coding: utf-8 -*-
"""
Created on 25 July 2016
@author: kylez
"""
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

requests.packages.urllib3.disable_warnings()


class ControllerProxy(object):

    def __init__(self, base_uri, *args, **kwargs):
        self.base_uri = base_uri
        self.session = requests.Session()

    @staticmethod
    def requests_retry_session(retries=3,
                               backoff_factor=0.3,
                               status_forcelist=(500, 502, 504),
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
        return self.requests_retry_session(session=self.session).get(uri, timeout=(10, 30), *args, **kwargs)

    def post_resource(self, resource, *args, **kwargs):
        uri = urljoin(self.base_uri, resource)
        return self.requests_retry_session(session=self.session).post(uri, timeout=(10, 30), *args, **kwargs)

    def request_resource(self, *args, **kwargs):
        return self.requests_retry_session(session=self.session).request(timeout=(10, 30), *args, **kwargs)
