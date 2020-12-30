# -*- coding: utf-8 -*-
"""
Test module for faucet.
@author: Charlie Lewis
"""
import os
import shutil
import tempfile

import yaml
from faucetconfgetsetter import FaucetLocalConfGetSetter
from poseidon_core.controllers.faucet.faucet import FaucetProxy
from poseidon_core.controllers.faucet.helpers import parse_rules
from poseidon_core.controllers.faucet.helpers import represent_none
from poseidon_core.controllers.faucet.helpers import yaml_in
from poseidon_core.controllers.faucet.helpers import yaml_out
from poseidon_core.helpers.config import Config


SAMPLE_CONFIG = 'tests/sample_faucet_config.yaml'


def _get_proxy(faucetconfgetsetter_cl, config=None, **kwargs):
    if config is None:
        config = Config().get_config()
    return FaucetProxy(config, faucetconfgetsetter_cl=faucetconfgetsetter_cl, **kwargs)


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

        config = Config().get_config()
        config['MIRROR_PORTS'] = {'foo': 1}
        config['ignore_vlans'] = ['foo']
        config['ignore_ports'] = [1]
        proxy = _get_proxy(faucetconfgetsetter_cl, config)


def test_format_endpoints():
    data = [[{'ip-state': 'foo'}, {'ip-state': 'bar'}],
            [{'ip-state': 'foo', 'ip-address': '0.0.0.0'}, {'ip-state': 'bar', 'ip-address': '::1'}]]
    output = FaucetProxy.format_endpoints(data)


def test_ignore_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl, ignore_vlans=[999], ignore_ports={'switch99': 11})
        for message_type in ('L2_LEARN',):
            assert faucet.ignore_event(
                {'dp_name': 'switch123', message_type: {'vid': 999, 'port_no': 123}})
            assert not faucet.ignore_event(
                {'dp_name': 'switch123', message_type: {'vid': 333, 'port_no': 123}})
            assert faucet.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 11}})
            assert not faucet.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 99}})
            assert faucet.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 99, 'stack_descr': 'something'}})
        assert faucet.ignore_event(
            {'dp_name': 'switch123', 'UNKNOWN': {'vid': 123, 'port_no': 123}})


def test_parse_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(SAMPLE_CONFIG, tmpdir)
        parse_rules(os.path.join(tmpdir, os.path.basename(SAMPLE_CONFIG)))


def test_clear_mirrors():
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        shutil.copy(SAMPLE_CONFIG, faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl, ignore_vlans=[999], ignore_ports={'switch99': 11})
        faucet.frpc.read_faucet_conf(
            config_file=faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        faucet.clear_mirrors()
        faucet.frpc.write_faucet_conf()


def test_represent_none():
    class MockDumper:
        def represent_scalar(self, foo, bar): return True

    foo = MockDumper()
    represent_none(foo, '')


def test_set_mirror_config():
    faucet_conf_str = """
dps:
    s1:
        interfaces:
            1:
                output_only: true
                mirror: [2]
            2:
                native_vlan: 100
            3:
                native_vlan: 100
"""

    def mirrors(faucet):
        faucet_conf = faucet.frpc.faucet_conf
        switch_conf = faucet_conf['dps']['s1']
        mirror_interface_conf = switch_conf['interfaces'][1]
        return mirror_interface_conf.get('mirror', None)

    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        faucet.frpc.faucet_conf = yaml.safe_load(
            faucet_conf_str)
        assert mirrors(faucet) == [2]
        faucet.frpc.mirror_port('s1', 1, 3)
        assert mirrors(faucet) == [2, 3]
        faucet.frpc.mirror_port('s1', 1, 2)
        assert mirrors(faucet) == [2, 3]
        faucet.frpc.clear_mirror_port('s1', 1)
        assert mirrors(faucet) is None


def test_stack_default_config():
    faucet_conf_str = """
dps:
    s1:
        stack:
            priority: 1
        dp_id: 0x1
        interfaces:
            1:
                output_only: true
            2:
                native_vlan: 100
            3:
                native_vlan: 100
            4:
                stack:
                    dp: s2
                    port: 4
    s2:
        dp_id: 0x2
        interfaces:
            1:
                output_only: true
            2:
                native_vlan: 100
            3:
                native_vlan: 100
            4:
                stack:
                    dp: s1
                    port: 4
acls:
    existing_acl:
        - rule:
            actions:
                allow: 1
"""
    new_faucet_conf_str = """
dps:
    s1:
        stack:
            priority: 1
        dp_id: 0x1
        arp_neighbor_timeout: 123
        timeout: 247
        interfaces:
            1:
                output_only: true
                description: Poseidon local mirror
            2:
                native_vlan: 100
            3:
                native_vlan: 100
            4:
                stack:
                    dp: s2
                    port: 4
    s2:
        dp_id: 0x2
        arp_neighbor_timeout: 123
        timeout: 247
        interfaces:
            1:
                description: Poseidon remote mirror (loopback plug)
                acls_in: [poseidon_tunnel]
                coprocessor:
                    strategy: vlan_vid
            2:
                native_vlan: 100
            3:
                native_vlan: 100
            4:
                stack:
                    dp: s1
                    port: 4
acls:
    existing_acl:
        - rule:
            actions:
                allow: 1
    poseidon_tunnel:
        - rule:
            vlan_vid: 999
            actions:
                allow: 0
        - rule:
            actions:
                allow: 0
                output:
                    tunnel:
                        type: vlan
                        tunnel_id: 999
                        dp: s1
                        port: 1
"""
    orig_faucet_conf = yaml.safe_load(faucet_conf_str)
    test_faucet_conf = yaml.safe_load(new_faucet_conf_str)
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1, 's2': 1},
            proxy_mirror_ports={'sx': ['s1', 99]},
            tunnel_vlan=999, tunnel_name='poseidon_tunnel')
        faucet.reinvestigation_frequency = 123
        faucet.frpc.faucet_conf = orig_faucet_conf
        faucet.frpc.write_faucet_conf()
        faucet._set_default_switch_conf()
        faucet.frpc.read_faucet_conf(config_file=None)
        assert faucet.frpc.faucet_conf['dps']['s1'] == test_faucet_conf['dps']['s1']
        assert faucet.frpc.faucet_conf['dps']['s2'] == test_faucet_conf['dps']['s2']
        assert faucet.frpc.faucet_conf['acls'] == test_faucet_conf['acls']


def test_proxy_mirror_config():
    faucet_conf_str = """
dps:
    s1:
        interfaces:
            1:
                output_only: true
            2:
                native_vlan: 100
            3:
                native_vlan: 100
            99:
                native_vlan: 100
    sx:
        interfaces:
            1:
                native_vlan: 100
"""
    faucet_conf = yaml.safe_load(faucet_conf_str)
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        # returns s1:99, not sx.
        faucet.frpc.faucet_conf = faucet_conf
        assert faucet.proxy_mirror_port('sx', 1) == ('s1', 99)


def test_check_mirror_config():
    faucet_conf_str = """
dps:
    s1:
        interfaces:
            1:
                output_only: true
                mirror: [2]
            2:
                native_vlan: 100
            3:
                native_vlan: 100
"""
    faucet_conf = yaml.safe_load(faucet_conf_str)
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(
            tmpdir, 'faucet.yaml')
        faucet = _get_proxy(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        faucet.frpc.faucet_conf = faucet_conf
        port = faucet.mirror_switch_port('s1')
        faucet.frpc.write_faucet_conf()
        assert port == 1
