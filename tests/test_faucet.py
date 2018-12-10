# -*- coding: utf-8 -*-
"""
Test module for faucet.
@author: Charlie Lewis
"""
import os

from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.helpers.config import Config


def test_get_endpoints():
    config_dir = '/etc/faucet'
    log_dir = '/var/log/faucet'
    if not os.path.exists(config_dir):
        config_dir = os.path.join(os.getcwd(), 'faucet')
    if not os.path.exists(log_dir):
        log_dir = os.path.join(os.getcwd(), 'faucet')

    try:
        f = open(os.path.join(log_dir, 'faucet.log'), 'r')
    except FileNotFoundError:
        f = open(os.path.join(log_dir, 'faucet.log'), 'w')
        f.write('Nov 19 18:52:31 faucet.valve INFO     DPID 123917682135854 (0x70b3d56cd32e) L2 learned b8:27:eb:ff:39:15 (L2 type 0x0800, L3 src 192.168.1.40) on Port 2 on VLAN 200 (2 hosts total)\n')
        f.write('Nov 19 18:52:31 faucet.valve INFO     DPID 123917682135854 (0x70b3d56cd32e) L2 learned b8:27:eb:ff:39:15 (L2 type 0x0800, L3 src 192.168.1.40) on Port 2 on VLAN 200 (2 hosts total)\n')
        f.write('Nov 19 18:52:31 faucet.valve INFO     DPID 123917682135854 (0x70b3d56cd32e) L2 learned b8:27:eb:ff:39:15 (L2 type 0x0800, L3 src 192.168.1.40) on Port 2 on VLAN 300 (2 hosts total)\n')
        f.write('Nov 19 18:52:31 faucet.valve INFO     DPID 123917682135854 (0x70b3d56cd32e) L2 learned b8:27:eb:cc:39:15 (L2 type 0x0800, L3 src 192.168.1.40) on Port 5 on VLAN 200 (2 hosts total)\n')
        f.write('Nov 19 18:52:31 faucet.valve INFO     DPID 123917682135854 (0x70b3d56cd32e) L2 learned b8:27:eb:cc:39:15 (L2 type 0x0800, L3 src 192.168.1.50) on Port 2 on VLAN 200 (2 hosts total)\n')
        f.write(
            'May 01 17:59:50 faucet.valve INFO     DPID 1 (0x1) 1 recently active hosts on VLAN 100, expired [00:00:00:00:00:01 on Port 1]\n')
        f.write(
            'May 01 18:02:15 faucet.valve INFO     DPID 1 (0x1) 0 recently active hosts on VLAN 100, expired [00:00:00:00:00:02 on Port 2]\n')
        f.write('foo\n')
        f.close()
    try:
        f = open(os.path.join(config_dir, 'faucet.yaml'), 'r')
    except FileNotFoundError:
        f = open(os.path.join(config_dir, 'faucet.yaml'), 'w')
        f.write('vlans:\n')
        f.write('    open:\n')
        f.write('        vid: 100\n')
        f.write('dps:\n')
        f.write('    switch1:\n')
        f.write('        dp_id: 0x70b3d56cd32e\n')
        f.write('        hardware: "ZodiacFX"\n')
        f.write('        proactive_learn: True\n')
        f.write('        interfaces:\n')
        f.write('            1:\n')
        f.write('                native_vlan: open\n')
        f.write('            2:\n')
        f.write('                native_vlan: open\n')
        f.write('            3:\n')
        f.write('                mirror: 1\n')
        f.write('                native_vlan: open\n')
        f.write('            4:\n')
        f.write('                native_vlan: open\n')
        f.write('            5:\n')
        f.write('                native_vlan: open\n')
        f.write('            6:\n')
        f.write('                native_vlan: open')

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
    proxy.get_switches()
    proxy.get_ports()
    proxy.get_vlans()
    proxy.get_span_fabric()
    proxy.get_byip('10.0.0.9')
    proxy.get_bymac('00:00:00:00:12:00')
    proxy.shutdown_ip('10.0.0.9')
    proxy.shutdown_endpoint()
    proxy.get_highest()
    proxy.get_seq_by_ip()
    proxy.mirror_mac('00:00:00:00:00:00')
    proxy.mirror_mac('00:00:00:00:00:01')
    proxy.unmirror_mac('00:00:00:00:00:00')

    proxy = FaucetProxy(controller)
    proxy.get_switches()
    proxy.get_ports()
    proxy.get_vlans()
    proxy.get_span_fabric()
    proxy.get_byip('10.0.0.9')
    proxy.get_bymac('00:00:00:00:12:00')
    proxy.shutdown_ip('10.0.0.9')
    proxy.shutdown_endpoint()
    proxy.get_highest()
    proxy.get_seq_by_ip()
    proxy.mirror_mac('00:00:00:00:00:00', messages=[{'dp_name': 'switch', 'L2_LEARN': {'l3_src_ip': '10.0.0.1', 'eth_src': '00:00:00:00:00:00', 'port_no': 1, 'vid': '100'}}, {
        'version': 1, 'time': 1525205350.0357792, 'dp_id': 1, 'dp_name': 'switch-1', 'event_id': 5, 'PORT_CHANGE': {'port_no': 1, 'reason': 'MODIFY', 'status': False}}, {}])
    proxy.mirror_mac('00:00:00:00:00:01')
    proxy.unmirror_mac('00:00:00:00:00:00', messages=[{'dp_name': 'switch', 'L2_LEARN': {'l3_src_ip': '10.0.0.1', 'eth_src': '00:00:00:00:00:00', 'port_no': 1, 'vid': '100'}}, {
        'version': 1, 'time': 1525205350.0357792, 'dp_id': 1, 'dp_name': 'switch-1', 'event_id': 5, 'PORT_CHANGE': {'port_no': 1, 'reason': 'MODIFY', 'status': False}}, {}])


def test_format_endpoints():
    data = [[{'ip-state': 'foo'}, {'ip-state': 'bar'}],
            [{'ip-state': 'foo'}, {'ip-state': 'bar'}]]
    output = FaucetProxy.format_endpoints(data)
