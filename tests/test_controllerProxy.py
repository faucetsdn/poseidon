# -*- coding: utf-8 -*-
"""
Test module for controllerproxy.
@author: kylez
"""
from poseidon.controllers.bcf.controllerproxy import ControllerProxy


def test_ControllerProxy():
    """
    Tests ControllerProxy
    # http://jsonplaceholder.typicode.com: Fake online REST API for testing.
    """
    proxy = ControllerProxy('http://jsonplaceholder.typicode.com')
    r = proxy.get_resource('posts')
    r.raise_for_status()
    r = proxy.post_resource('posts')
    r.raise_for_status()
    r = proxy.request_resource(
        method='PUT',
        url='http://jsonplaceholder.typicode.com/posts/1')
    r.raise_for_status()
