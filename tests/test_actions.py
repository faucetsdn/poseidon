# -*- coding: utf-8 -*-
"""
Test module for actions
@author: Charlie Lewis
"""
import logging

from faucetconfgetsetter import get_sdn_connect
from poseidon_core.helpers.actions import Actions
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import endpoint_factory

logger = logging.getLogger('test')


def test_Actions():
    """
    Tests Actions
    """
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s = get_sdn_connect(logger)
    a = Actions(endpoint, s.sdnc)
    a.mirror_endpoint()
    a.unmirror_endpoint()
    a.coprocess_endpoint()
    a.uncoprocess_endpoint()


def test_Actions_nosdn():
    """
    Tests Actions with no SDN controller
    """
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s = get_sdn_connect(logger)
    s.sdnc = None
    a = Actions(endpoint, s.sdnc)
    a.mirror_endpoint()
    a.unmirror_endpoint()
    a.coprocess_endpoint()
    a.uncoprocess_endpoint()
