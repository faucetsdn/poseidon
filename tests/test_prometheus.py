# -*- coding: utf-8 -*-
"""
Test module for prometheus
@author: Charlie Lewis
"""
from poseidon.helpers.prometheus import Prometheus


def test_Prometheus():
    """
    Tests Prometheus
    """
    p = Prometheus.get_metrics()
    p.initialize_metrics()
    hosts = [{'active': 0, 'record_source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ip': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'hash': 'foo1', 'behavior': 1},
             {'active': 1, 'record_source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ip': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'hash': 'foo2', 'behavior': 1},
             {'active': 0, 'record_source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ip': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'hash': 'foo3', 'behavior': 1},
             {'active': 1, 'record_source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ip': '2106::1', 'mac': '00:00:00:00:00:00', 'hash': 'foo4', 'behavior': 1},
             {'active': 1, 'record_source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ip': '::', 'mac': '00:00:00:00:00:00', 'hash': 'foo5', 'behavior': 1}]
    p = Prometheus()
    p.update_metrics(hosts)
