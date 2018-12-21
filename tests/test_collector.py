# -*- coding: utf-8 -*-
"""
Test module for vent collector.
@author: Charlie Lewis
"""
from poseidon.helpers.collector import Collector
from poseidon.helpers.endpoint import Endpoint


def test_Collector():
    """
    Tests Collector
    """
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'mac': '00:00:00:00:00:00'}
    a = Collector(endpoint)
    a.start_vent_collector()
    a.get_vent_collectors()
    a.host_has_active_collectors('foo')
