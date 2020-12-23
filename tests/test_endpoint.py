# -*- coding: utf-8 -*-
"""
Test module for endpoints.
@author: Charlie Lewis
"""
import time

from poseidon_core.helpers.endpoint import Endpoint
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.helpers.endpoint import EndpointDecoder


def test_Endpoint():
    """Tests Endpoint."""
    endpoint = endpoint_factory('foo')
    b = endpoint.encode()
    c = EndpointDecoder(b).get_endpoint()
    a = {'tenant': 'foo', 'mac': '00:00:00:00:00:00'}
    assert Endpoint.make_hash(a)


def test_times_next():
    endpoint = endpoint_factory('foo')
    endpoint.queue_next('operate')
    time.sleep(1)
    endpoint.copro_queue_next('copro_coprocess')
    time.sleep(1)
    assert endpoint.state_timeout(0)
    assert endpoint.copro_state_timeout(0)
    endpoint.trigger_next()
    endpoint.copro_trigger_next()
