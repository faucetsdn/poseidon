# -*- coding: utf-8 -*-
"""
Test module for faucet parser.
@author: Charlie Lewis
"""
import copy
import os
import shutil
import tempfile
import yaml
from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.controllers.faucet.helpers import get_config_file, parse_rules, represent_none
from poseidon.controllers.faucet.parser import Parser, FaucetLocalConfGetSetter
from poseidon.helpers.config import Config
from poseidon.helpers.endpoint import endpoint_factory


SAMPLE_CONFIG = 'tests/sample_faucet_config.yaml'


def _get_parser(faucetconfgetsetter_cl=FaucetLocalConfGetSetter, **kwargs):
    return Parser(faucetconfgetsetter_cl=faucetconfgetsetter_cl, **kwargs)


def _get_proxy(controller=None, faucetconfgetsetter_cl=FaucetLocalConfGetSetter):
    if controller is None:
        controller = Config().get_config()
    return FaucetProxy(controller, faucetconfgetsetter_cl=faucetconfgetsetter_cl)


def test_ignore_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl, ignore_vlans=[999], ignore_ports={'switch99': 11})
        for message_type in ('L2_LEARN', 'L2_EXPIRE', 'PORT_CHANGE'):
            assert parser.ignore_event(
                {'dp_name': 'switch123', message_type: {'vid': 999, 'port_no': 123}})
            assert not parser.ignore_event(
                {'dp_name': 'switch123', message_type: {'vid': 333, 'port_no': 123}})
            assert parser.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 11}})
            assert not parser.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 99}})
            assert parser.ignore_event(
                {'dp_name': 'switch99', message_type: {'vid': 333, 'port_no': 99, 'stack_descr': 'something'}})
        assert parser.ignore_event(
            {'dp_name': 'switch123', 'UNKNOWN': {'vid': 123, 'port_no': 123}})


def test_parse_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(SAMPLE_CONFIG, tmpdir)
        parse_rules(os.path.join(tmpdir, os.path.basename(SAMPLE_CONFIG)))


def test_clear_mirrors():
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        shutil.copy(SAMPLE_CONFIG, faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl, ignore_vlans=[999], ignore_ports={'switch99': 11})
        parser.faucetconfgetsetter.read_faucet_conf(config_file=faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        parser.clear_mirrors()
        parser.faucetconfgetsetter.write_faucet_conf()


def test_represent_none():
    class MockDumper:
        def represent_scalar(self, foo, bar): return True

    foo = MockDumper()
    represent_none(foo, '')


def test_get_config_file():
    config = get_config_file(None)
    assert config == '/etc/faucet/faucet.yaml'


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
    faucet_conf = yaml.safe_load(faucet_conf_str)
    switch_conf = faucet_conf['dps']['s1']
    mirror_interface_conf = switch_conf['interfaces'][1]
    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        parser.faucetconfgetsetter.faucet_conf = faucet_conf
        assert mirror_interface_conf['mirror'] == [2]
        parser.faucetconfgetsetter.set_mirror_config('s1', 1, 3)
        assert mirror_interface_conf['mirror'] == [3]
        parser.faucetconfgetsetter.write_faucet_conf()
        parser.faucetconfgetsetter.set_mirror_config('s1', 1, [2, 3])
        assert mirror_interface_conf['mirror'] == [2, 3]
        parser.faucetconfgetsetter.write_faucet_conf()
        parser.faucetconfgetsetter.set_mirror_config('s1', 1, None)
        assert 'mirror' not in mirror_interface_conf
        parser.faucetconfgetsetter.write_faucet_conf()


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
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1, 's2': 1},
            proxy_mirror_ports={'sx': ['s1', 99]},
            tunnel_vlan=999, tunnel_name='poseidon_tunnel')
        parser.reinvestigation_frequency = 123
        parser.faucetconfgetsetter.faucet_conf = orig_faucet_conf
        parser.faucetconfgetsetter.write_faucet_conf()
        parser._set_default_switch_conf()
        parser._read_faucet_conf()
        assert parser.faucetconfgetsetter.faucet_conf['dps']['s1'] == test_faucet_conf['dps']['s1']
        assert parser.faucetconfgetsetter.faucet_conf['dps']['s2'] == test_faucet_conf['dps']['s2']
        assert parser.faucetconfgetsetter.faucet_conf['acls'] == test_faucet_conf['acls']


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
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        # returns s1:99, not sx.
        parser.faucetconfgetsetter.faucet_conf = faucet_conf
        assert parser.proxy_mirror_port('sx', 1) == ('s1', 99)


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
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'s1': 1},
            proxy_mirror_ports={'sx': ['s1', 99]})
        parser.faucetconfgetsetter.faucet_conf = faucet_conf
        port, mirror_ports = parser.check_mirror('s1')
        parser.faucetconfgetsetter.write_faucet_conf()
        assert port == 1
        assert mirror_ports == {2}


def test_Parser():
    """
    Tests Parser
    """
    def check_config(obj, endpoints):
        obj.config('mirror', 1, 't1-1')
        obj.config('mirror', 2, 0x1)
        obj.config('mirror', 2, 't1-1')
        obj.config('mirror', 5, 't2-1')
        obj.config('mirror', 6, 'bad')
        obj.config('unmirror', None, None)
        obj.config('unmirror', 1, 't1-1')
        obj.config('unmirror', 1, 't1-1')
        obj.config('shutdown', None, None)
        obj.config('apply_acls', None, None)
        obj.config('apply_acls', 1, 't1-1', endpoints=endpoints,
                   rules_file=os.path.join(os.getcwd(), 'rules.yaml'))
        obj.config('unknown', None, None)

    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 't1-1', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'1551805502.0': {'labels': ['developer workstation'], 'behavior': 'normal'}}}, 'ipv4_addresses': {
        '0.0.0.0': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
    endpoints = [endpoint]

    with tempfile.TemporaryDirectory() as tmpdir:
        faucetconfgetsetter_cl = FaucetLocalConfGetSetter
        faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE = os.path.join(tmpdir, 'faucet.yaml')
        shutil.copy(SAMPLE_CONFIG, faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        parser = _get_parser(
            faucetconfgetsetter_cl=faucetconfgetsetter_cl,
            mirror_ports={'t1-1': 2},
            proxy_mirror_ports={'sx': ['s1', 99]})
        parser.faucetconfgetsetter.faucet_conf = yaml.safe_load(faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        parser2 = _get_parser(faucetconfgetsetter_cl=faucetconfgetsetter_cl)
        parser2.faucetconfgetsetter.faucet_conf = yaml.safe_load(faucetconfgetsetter_cl.DEFAULT_CONFIG_FILE)
        controller = Config().get_config()
        proxy = _get_proxy(faucetconfgetsetter_cl=faucetconfgetsetter_cl, controller=controller)
        check_config(parser, endpoints)
        check_config(parser2, endpoints)
        check_config(proxy, endpoints)
