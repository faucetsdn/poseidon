# -*- coding: utf-8 -*-
"""
Test module for redis.py

Created on 28 June 2016
@author: Charlie Lewis, dgrossman, MShel
"""
import logging

from pytest_redis import factories

from poseidon.helpers.endpoint import endpoint_factory
from poseidon.helpers.redis import PoseidonRedisClient

redis_my_proc = factories.redis_proc(port=None)
redis_my = factories.redisdb('redis_my_proc')


def test_redis_smoke(redis_my, redis_my_proc):
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    prc = PoseidonRedisClient(
        logger, host='localhost', port=redis_my_proc.port)
    prc.connect()
    prc.r.flushall()
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'1551805502': {'labels': ['developer workstation']}}}, 'ipv4_addresses': {
        '0.0.0.0': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
    endpoints = {endpoint.name: endpoint}
    prc.store_endpoints(endpoints)
    stored_endpoints = prc.get_stored_endpoints()
    stored_endpoint = stored_endpoints[endpoint.name]
    assert endpoint.endpoint_data == stored_endpoint.endpoint_data
    assert endpoint.metadata == stored_endpoint.metadata


def test_update_networkml(redis_my, redis_my_proc):
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    prc = PoseidonRedisClient(
        logger, host='localhost', port=redis_my_proc.port)
    prc.connect()
    prc.r.flushall()
    source_mac = '00:00:00:00:00:00'
    ipv4 = '1.2.3.4'
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': source_mac, 'segment': 'foo', 'port': '1', 'ipv4': ipv4, 'ipv6': '1212::1'}
    endpoints = {endpoint.name: endpoint}
    prc.store_endpoints(endpoints)
    networkml_results = {
        'id': '', 'type': 'metadata', 'results': {'tool': 'networkml', 'version': 'aversion'},
        'file_path': '/files/trace_%s_05-06_23_50_49.pcap' % endpoint.name,
        'data': {
            endpoint.name: {
                'valid': 'true', 'pcap_labels': 'null',
                'decisions': {'investigate': 'false'},
                'classification': {
                    'labels': ['role1', 'role2', 'role3'],
                    'confidences': [0.9, 0.8, 0.7]},
                'timestamp': 999.123, 'source_ip': ipv4, 'source_mac': source_mac},
            'pcap': 'trace_%s_2020-05-06_23_50_49.pcap' % endpoint.name}}
    prc.store_tool_result(networkml_results, 'networkml')
    good_pof_results = {
        ipv4: {'full_os': 'Linux 2.2.x-3.x', 'short_os': 'Linux', 'link': 'Ethernet or modem', 'raw_mtu': '1500', 'mac': source_mac}}
    prc.store_p0f_result(good_pof_results)
    prc.store_endpoints(endpoints)
    stored_endpoints = prc.get_stored_endpoints()
    stored_endpoint = stored_endpoints[endpoint.name]
    timestamp = list(
        stored_endpoint.metadata['mac_addresses'][source_mac].keys())[0]
    correlated_metadata = {
        'mac_addresses': {source_mac: {timestamp: {'labels': ['role1', 'role2', 'role3'], 'confidences': [0.9, 0.8, 0.7], 'pcap_labels': 'null'}}},
        'ipv4_addresses': {ipv4: {'os': 'Linux'}}, 'ipv6_addresses': {'1212::1': {}}}
    assert endpoint.metadata == correlated_metadata
    bad_pof_results = {
        ipv4: {'full_os': '', 'short_os': '', 'link': '', 'raw_mtu': '', 'mac': source_mac}}
    prc.store_p0f_result(bad_pof_results)
    prc.store_endpoints(endpoints)
    stored_endpoints = prc.get_stored_endpoints()
    stored_endpoint = stored_endpoints[endpoint.name]
    # empty p0f doesn't overwrite
    assert endpoint.metadata == correlated_metadata


def test_update_history():
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'1551805502': {'labels': ['developer workstation']}}}, 'ipv4_addresses': {
        '0.0.0.0': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
    metadata = {123: {'foo': 'bar'}}
    logger = logging.getLogger('test')
    prc = PoseidonRedisClient(logger)
    prc.update_history(endpoint, {'00:00:00:00:00:00': metadata}, {
                       '0.0.0.0': metadata}, {'1212::1': metadata})


def test_parse_networkml_metadata():
    logger = logging.getLogger('test')
    prc = PoseidonRedisClient(logger)
    mac_info = {
        b'poseidon_hash': 'myhash',
    }
    ml_info = {
        'myhash': b'{"pcap_labels": "mylabels", "classification": {"labels": ["foo", "bar"], "confidences": [1.0, 2.0]}}',
    }
    assert prc.parse_networkml_metadata(mac_info, ml_info) == {
        'confidences': [1.0, 2.0],
        'labels': ['foo', 'bar'], 'pcap_labels': 'mylabels'}
    ml_info = {
        'notmyhash': b'{"pcap_labels": "mylabels", "classification": {"labels": ["foo", "bar"], "confidences": [1.0, 2.0]}}',
    }
    assert prc.parse_networkml_metadata(mac_info, ml_info) == {}
