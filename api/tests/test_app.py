import falcon
import os
import redis
from falcon import testing
import pytest

from app.app import api


@pytest.fixture
def client():
    return testing.TestClient(api)


def test_setup_redis():
    if 'POSEIDON_TRAVIS' in os.environ:
        r = redis.StrictRedis(host='localhost',
                              port=6379,
                              db=0,
                              decode_responses=True)
    else:
        r = redis.StrictRedis(host='redis',
                              port=6379,
                              db=0,
                              decode_responses=True)
    r.sadd('ip_addresses', '10.0.0.1')
    r.sadd('ip_addresses', '10.0.0.2')
    r.sadd('ip_addresses', '10.0.0.3')
    r.sadd('ip_addresses', '2601:645:8200:a571:18fd:6640:9cd9:10d3')
    r.hmset('10.0.0.1',
            {'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f81',
             'timestamps': "['1527208227']",
             'short_os': 'Mac'})
    r.hmset('10.0.0.2',
            {'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f82',
             'timestamps': "['1527208220', '1527208227']",
             'short_os': 'Windows'})
    r.hmset('10.0.0.3',
            {'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f83',
             'timestamps': "['1527208220', '1527208228']",
             'short_os': 'Linux'})
    r.hmset('10.0.0.1_1527208227', {'labels': ["Developer workstation",
                                               "Unknown",
                                               "Smartphone"],
                                    'confidences': [0.6065386838895384,
                                                    0.3487681867266965,
                                                    0.015645883198622094]})
    r.hmset('10.0.0.2_1527208227', {'labels': ["Developer workstation",
                                               "Unknown",
                                               "Smartphone"],
                                    'confidences': [0.6065386838895384,
                                                    0.3487681867266965,
                                                    0.015645883198622094]})
    r.hmset('10.0.0.3_1527208228', {'labels': ["Developer workstation",
                                               "Unknown",
                                               "Smartphone"],
                                    'confidences': [0.6065386838895384,
                                                    0.3487681867266965,
                                                    0.015645883198622094]})
    r.hmset('6cd09124a66ef1bbc72c1aff4e333766d3533f81',
            {"transition_time": "1524623228.1019075",
             "prev_state": "None",
             "endpoint_data": "{'name': None, \
                                'mac': '00:00:00:00:00:01', \
                                'ip-address': '10.0.0.1', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'KNOWN'}",
             "next_state": "REINVESTIGATING",
             "state": "KNOWN"})
    r.hmset('6cd09124a66ef1bbc72c1aff4e333766d3533f82',
            {"transition_time": "1524623228.1019075",
             "prev_state": "None",
             "endpoint_data": "{'name': None, \
                                'mac': '00:00:00:00:00:02', \
                                'ip-address': '10.0.0.2', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'KNOWN'}",
             "next_state": "REINVESTIGATING",
             "state": "KNOWN"})
    r.hmset('6cd09124a66ef1bbc72c1aff4e333766d3533f83',
            {"transition_time": "1524623228.1019075",
             "prev_state": "None",
             "endpoint_data": "{'name': None, \
                                'mac': '00:00:00:00:00:03', \
                                'ip-address': '10.0.0.3', \
                                'segment': '1', \
                                'port': '1', \
                                'tenant': 'VLAN100', \
                                'state': 'KNOWN'}",
             "next_state": "REINVESTIGATING",
             "state": "KNOWN"})


def test_v1(client):
    response = client.simulate_get('/v1')
    assert response.status == falcon.HTTP_OK


def test_network(client):
    response = client.simulate_get('/v1/network')
    assert len(response.json) == 2
    assert response.status == falcon.HTTP_OK


def test_network_full(client):
    response = client.simulate_get('/v1/network_full')
    assert len(response.json) == 1
    assert response.status == falcon.HTTP_OK


def test_info(client):
    response = client.simulate_get('/v1/info')
    assert response.status == falcon.HTTP_OK
