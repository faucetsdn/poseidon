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
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {'mac': '00:00:00:00:00:00'}
    a = Collector(endpoint, 'foo')
    a.start_vent_collector()
    a.stop_vent_collector()
    a.get_vent_collectors()
    a.host_has_active_collectors('foo')
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'container_id': 'foo'}
    a = Collector(endpoint, 'foo')
    a.stop_vent_collector()
