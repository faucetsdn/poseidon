# -*- coding: utf-8 -*-
"""
Test module for actions
@author: Charlie Lewis
"""
from poseidon.helpers.actions import Actions
from poseidon.helpers.endpoint import Endpoint
from poseidon.main import SDNConnect


def test_Actions():
    """
    Tests Actions
    """
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s = SDNConnect()
    a = Actions(endpoint, s.sdnc)
    a.mirror_endpoint()
    a.unmirror_endpoint()
    a.shutdown_endpoint()
