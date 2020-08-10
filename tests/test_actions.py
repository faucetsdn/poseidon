# -*- coding: utf-8 -*-
"""
Test module for actions
@author: Charlie Lewis
"""
from poseidon.helpers.actions import Actions
from poseidon.helpers.config import Config
from poseidon.helpers.endpoint import endpoint_factory
from poseidon.main import SDNConnect


def get_test_controller():
    controller = Config().get_config()
    controller['faucetconfrpc_address'] = None
    controller['TYPE'] = 'faucet'
    return controller


def test_Actions():
    """
    Tests Actions
    """
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    controller = get_test_controller()
    s = SDNConnect(controller)
    a = Actions(endpoint, s.sdnc)
    a.mirror_endpoint()
    a.unmirror_endpoint()
    a.coprocess_endpoint()
    a.uncoprocess_endpoint()
    a.shutdown_endpoint()


def test_Actions_nosdn():
    """
    Tests Actions with no SDN controller
    """
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    controller = get_test_controller()
    s = SDNConnect(controller)
    s.sdnc = None
    a = Actions(endpoint, s.sdnc)
    a.mirror_endpoint()
    a.unmirror_endpoint()
    a.coprocess_endpoint()
    a.uncoprocess_endpoint()
    a.shutdown_endpoint()
