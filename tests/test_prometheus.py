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
    hosts = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2'},
             {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3'},
             {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5'}]
    p = Prometheus()
    p.update_metrics(hosts)


def test_decode_endpoints():
    p = Prometheus()
    hashes = {
        '6b33db53faf33c77d694ecab2e3fefadc7dacc70': {'__name__': 'poseidon_endpoint_metadata', 'acls': '[]', 'controller_type': 'faucet', 'ether_vendor': 'Micro-Star', 'hash_id': '6b33db53faf33c77d694ecab2e3fefadc7dacc70', 'ignore': 'False', 'instance': 'poseidon:9304', 'ipv4_address': '192.168.3.131', 'ipv4_os': 'Windows', 'ipv4_rdns': 'NO DATA', 'ipv4_subnet': '192.168.3.0/24', 'ipv6_subnet': 'NO DATA', 'job': 'poseidon', 'mac': '40:61:86:9a:f1:f5', 'name': 'None', 'next_state': 'None', 'port': '1', 'prev_state': 'queued', 'segment': 'switch1', 'state': 'mirroring', 'tenant': 'VLAN100', 'top_role': 'Administrator workstation'}}
    role_hashes = {
        '6b33db53faf33c77d694ecab2e3fefadc7dacc70': {'mac': '40:61:86:9a:f1:f5', 'pcap_labels': 'foo', 'top_confidence': 1.0, 'state': 'mirroring', 'top_role': 'Administrator workstation', 'second_role': 'GPU laptop', 'second_confidence': 0.0006269307506632729, 'third_role': 'Developer workstation', 'third_confidence': 0.000399485844886532}}
    endpoints = p.prom_endpoints(hashes, role_hashes)
    endpoint = endpoints['6b33db53faf33c77d694ecab2e3fefadc7dacc70']
    assert endpoint.state == 'mirroring'
    assert endpoint.get_ipv4_os() == 'Windows'
    roles, confidences, pcap_labels = endpoint.get_roles_confidences_pcap_labels()
    assert roles == ('Administrator workstation', 'GPU laptop', 'Developer workstation')
    assert confidences == (1.0, 0.0006269307506632729, 0.000399485844886532)
    assert pcap_labels == 'foo'
