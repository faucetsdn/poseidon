import falcon
import redis
from falcon import testing
import pytest

from app.app import api


@pytest.fixture
def client():
    return testing.TestClient(api)


def test_setup_redis():
    try:
        r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
        r.sadd('ip_addresses', '10.0.0.1')
        r.hmset('10.0.0.1', {'poseidon_hash': '6cd09124a66ef1bbc72c1aff4e333766d3533f81'})
        r.hmset('6cd09124a66ef1bbc72c1aff4e333766d3533f81', {"transition_time":"1524623228.1019075", "prev_state":"None", "endpoint_data":"{'name': None, 'mac': '00:00:00:00:00:01', 'ip-address': '10.0.0.1', 'segment': '1', 'port': '1', 'tenant': 'VLAN100'}", "next_state":"REINVESTIGATING", "state":"KNOWN"})
    except Exception as e:
        pass


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
