# -*- coding: utf-8 -*-
"""
Test module for faucet.
@author: Charlie Lewis
"""
import os
import shutil
import tempfile

from poseidon_core.controllers.faucet.faucet import FaucetProxy
from poseidon_core.controllers.faucet.helpers import yaml_in
from poseidon_core.controllers.faucet.helpers import yaml_out
from poseidon_core.controllers.faucet.parser import FaucetLocalConfGetSetter
from poseidon_core.helpers.config import Config

SAMPLE_CONFIG = 'tests/sample_faucet_config.yaml'


def _get_proxy(faucetconfgetsetter_cl, controller=None):
    if controller is None:
        controller = Config().get_config()
    return FaucetProxy(controller, faucetconfgetsetter_cl=faucetconfgetsetter_cl)


def test_yaml_in():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_yaml_file = os.path.join(tmpdir, 'test.yaml')
        content = {'test': 'content'}
        yaml_out(test_yaml_file, content)
        assert yaml_in(test_yaml_file) == content


def test_get_endpoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        shutil.copy(SAMPLE_CONFIG, faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        proxy = _get_proxy(faucetconfgetsetter_cl)
        a = proxy.get_endpoints()
        assert isinstance(a, list)

        proxy = _get_proxy(faucetconfgetsetter_cl)
        a = proxy.get_endpoints(messages=[{'dp_name': 'switch', 'L2_LEARN': {'l3_src_ip': '10.0.0.1', 'eth_src': '00:00:00:00:00:00', 'port_no': 1, 'vid': '100'}}, {
                                'version': 1, 'time': 1525205350.0357792, 'dp_id': 1, 'dp_name': 'switch-1', 'event_id': 5, 'PORT_CHANGE': {'port_no': 1, 'reason': 'MODIFY', 'status': False}}, {}])
        assert isinstance(a, list)


def test_FaucetProxy():
    """
    Tests Faucet
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        shutil.copy(SAMPLE_CONFIG, faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        proxy = _get_proxy(faucetconfgetsetter_cl)
        proxy.mirror_mac('00:00:00:00:00:00', None, None)
        proxy.mirror_mac('00:00:00:00:00:01', None, None)
        proxy.unmirror_mac('00:00:00:00:00:00', None, None)
        proxy.update_acls()

        proxy = _get_proxy(faucetconfgetsetter_cl)
        proxy.mirror_mac('00:00:00:00:00:00', None, None)
        proxy.mirror_mac('00:00:00:00:00:01', None, None)
        proxy.unmirror_mac('00:00:00:00:00:00', None, None)
        proxy.update_acls()

        controller = Config().get_config()
        controller['MIRROR_PORTS'] = {'foo': 1}
        controller['ignore_vlans'] = ['foo']
        controller['ignore_ports'] = [1]
        proxy = _get_proxy(faucetconfgetsetter_cl, controller)


def test_format_endpoints():
    data = [[{'ip-state': 'foo'}, {'ip-state': 'bar'}],
            [{'ip-state': 'foo', 'ip-address': '0.0.0.0'}, {'ip-state': 'bar', 'ip-address': '::1'}]]
    output = FaucetProxy.format_endpoints(data)
