# -*- coding: utf-8 -*-
"""
Test module for faucet.
@author: Charlie Lewis
"""
import os
import tempfile
from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.helpers.config import Config
from poseidon.controllers.faucet.helpers import yaml_in, yaml_out


def test_yaml_in():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_yaml_file = os.path.join(tmpdir, 'test.yaml')
        content = {'test': 'content'}
        yaml_out(test_yaml_file, content)
        assert yaml_in(test_yaml_file) == content


def test_get_endpoints():
    controller = Config().get_config()
    proxy = FaucetProxy(controller)
    a = proxy.get_endpoints()
    assert isinstance(a, list)

    proxy = FaucetProxy(controller)
    a = proxy.get_endpoints(messages=[{'dp_name': 'switch', 'L2_LEARN': {'l3_src_ip': '10.0.0.1', 'eth_src': '00:00:00:00:00:00', 'port_no': 1, 'vid': '100'}}, {
                            'version': 1, 'time': 1525205350.0357792, 'dp_id': 1, 'dp_name': 'switch-1', 'event_id': 5, 'PORT_CHANGE': {'port_no': 1, 'reason': 'MODIFY', 'status': False}}, {}])
    assert isinstance(a, list)


def test_FaucetProxy():
    """
    Tests Faucet
    """
    controller = Config().get_config()
    proxy = FaucetProxy(controller)
    proxy.shutdown_ip('10.0.0.9')
    proxy.shutdown_endpoint()
    proxy.mirror_mac('00:00:00:00:00:00', None, None)
    proxy.mirror_mac('00:00:00:00:00:01', None, None)
    proxy.unmirror_mac('00:00:00:00:00:00', None, None)
    proxy.update_acls()

    proxy = FaucetProxy(controller)
    proxy.shutdown_ip('10.0.0.9')
    proxy.shutdown_endpoint()
    proxy.mirror_mac('00:00:00:00:00:00', None, None)
    proxy.mirror_mac('00:00:00:00:00:01', None, None)
    proxy.unmirror_mac('00:00:00:00:00:00', None, None)
    proxy.update_acls()

    controller = Config().get_config()
    controller['MIRROR_PORTS'] = '{"foo":1}'
    controller['ignore_vlans'] = ['foo']
    controller['ignore_ports'] = [1]
    proxy = FaucetProxy(controller)


def test_format_endpoints():
    data = [[{'ip-state': 'foo'}, {'ip-state': 'bar'}],
            [{'ip-state': 'foo', 'ip-address': '0.0.0.0'}, {'ip-state': 'bar', 'ip-address': '::1'}]]
    output = FaucetProxy.format_endpoints(data)
