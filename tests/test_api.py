
import falcon
import pytest
import redis
from pytest_redis import factories
from falcon import testing

from api.app.app import api


redis_my_proc = factories.redis_proc(port=6379)
redis_my = factories.redisdb('redis_my_proc')


@pytest.fixture
def client():
    return testing.TestClient(api)


def setup_redis():
    r = redis.StrictRedis(host='localhost',
                          port=6379,
                          db=0,
                          decode_responses=True)
    r.sadd('ip_addresses', '10.0.0.1')
    r.sadd('ip_addresses', 'None')
    r.sadd('ip_addresses', '2601:645:8200:a571:18fd:6640:9cd9:10d3')
    r.sadd('mac_addresses', '00:00:00:00:00:01')
    r.sadd('mac_addresses', '00:00:00:00:00:02')
    r.sadd('mac_addresses', '00:00:00:00:00:03')

    r.hset(
        'p0f_10.0.0.1', mapping={'timestamps': "['1527208227']", 'short_os': 'Mac'})
    r.hset(
        'p0f_None', mapping={'timestamps': "['1527208220', '1527208227']", 'short_os': 'Windows'})
    r.hset(
        'p0f_2601:645:8200:a571:18fd:6640:9cd9:10d3', mapping={'timestamps': "['1527208220', '1527208228']", 'short_os': 'Linux'})

    r.hset(
        '00:00:00:00:00:01', mapping={'timestamps': "['1527208227']", 'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f81'})
    r.hset(
        '00:00:00:00:00:02', mapping={'timestamps': "['1527208220', '1527208227']", 'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f82'})
    r.hset(
        '00:00:00:00:00:03', mapping={'timestamps': "['1527208220', '1527208228']", 'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f83'})

    for key, name in (
            ('networkml_00:00:00:00:00:01_1527208227', '6cd09124a66ef1bbc72c1aff4e333766d3533f81'),
            ('networkml_00:00:00:00:00:02_1527208227', '6cd09124a66ef1bbc72c1aff4e333766d3533f82'),
            ('networkml_00:00:00:00:00:03_1527208228', '6cd09124a66ef1bbc72c1aff4e333766d3533f83')):
        r.hset(key, mapping={
            name: "{'decisions':{'behavior': 'normal'}, 'classification': {'confidences': [0.606, 0.348, 0.015], 'labels': ['Developer workstation', 'Unknown', 'Smartphone']}}"})

    r.hset('6cd09124a66ef1bbc72c1aff4e333766d3533f81',
            mapping={'transition_time': '1524623228.1019075',
             'endpoint_data': "{'name': None, \
                                'prev_state': None, \
                                'mac': '00:00:00:00:00:01', \
                                'ipv4': '10.0.0.1', \
                                'ipv6': '', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'UNKNOWN', \
                                'active': 0}",
             'next_state': 'REINVESTIGATING',
             'state': 'KNOWN'})
    r.hset('6cd09124a66ef1bbc72c1aff4e333766d3533f82',
            mapping={'transition_time': '1524623228.1019075',
             'endpoint_data': "{'name': None, \
                                'prev_state': None, \
                                'mac': '00:00:00:00:00:02', \
                                'ipv4': 'None', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'UNKNOWN', \
                                'active': 1}",
             'next_state': 'REINVESTIGATING',
             'state': 'KNOWN'})
    r.hset('6cd09124a66ef1bbc72c1aff4e333766d3533f83',
            mapping={'transition_time': '1524623228.1019075',
             'endpoint_data': "{'name': None, \
                                'prev_state': None, \
                                'mac': '00:00:00:00:00:03', \
                                'ipv6': '2601:645:8200:a571:18fd:6640:9cd9:10d3', \
                                'ipv4': '', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'UNKNOWN', \
                                'active': 1}",
             'next_state': 'REINVESTIGATING',
             'ignore': 'False',
             'prev_state': "('UNKNOWN', 1527208228)",
             'state': 'KNOWN'})


def verify_endpoints(response):
    assert response.json['dataset']
    nodes = {node['id']: node for node in response.json['dataset']}
    first_node = nodes['6cd09124a66ef1bbc72c1aff4e333766d3533f81']
    assert first_node['mac'] == '00:00:00:00:00:01'
    assert first_node['ipv4_os'] == 'Mac'
    assert first_node['ipv4'] == '10.0.0.1'
    assert first_node['ipv4_subnet'] == '10.0.0.0/24'
    third_node = nodes['6cd09124a66ef1bbc72c1aff4e333766d3533f83']
    assert third_node['role'] == 'Developer workstation'
    assert third_node['ipv6'] == '2601:645:8200:a571:18fd:6640:9cd9:10d3'
    assert third_node['ipv6_subnet'] == '2601:645:8200:a571::/64'


def test_v1(client, redis_my):
    setup_redis()
    response = client.simulate_get('/v1')
    assert response.status == falcon.HTTP_OK


def test_network(client, redis_my):
    setup_redis()
    response = client.simulate_get('/v1/network')
    assert len(response.json) == 2
    assert response.status == falcon.HTTP_OK
    verify_endpoints(response)


def test_network_by_ip(client, redis_my):
    setup_redis()
    response = client.simulate_get('/v1/network/10.0.0.1')
    assert len(response.json['dataset']) == 1
    assert response.status == falcon.HTTP_OK


def test_network_full(client, redis_my):
    setup_redis()
    response = client.simulate_get('/v1/network_full')
    assert len(response.json) == 1
    assert response.status == falcon.HTTP_OK
    verify_endpoints(response)


def test_info(client, redis_my):
    response = client.simulate_get('/v1/info')
    assert response.status == falcon.HTTP_OK
