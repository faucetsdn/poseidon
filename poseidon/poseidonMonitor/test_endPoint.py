"""
Test module for endPoint.py

Created on 2 October 2017
@author: Jorissss
"""
import pytest

from poseidon.poseidonMonitor import endPoint

test_data = {u'tenant': u'FLOORPLATE',
             u'mac': u'de:ad:be:ef:7f:12',
             u'segment': u'prod',
             u'name': None,
             u'ip-address': u'102.179.20.100'}


def test_endpoint_creation_no_state():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint2 = endPoint.EndPoint.from_json(endpoint1.to_json())
1
    assert endpoint1.make_hash() == endpoint2.make_hash()

def test_endpoint_creation_with_state():
    endpoint0 = endPoint.EndPoint(test_data)
    endpoint1 = endPoint.EndPoint(test_data, state='TEST1')
    endpoint2 = endPoint.EndPoint(test_data, next_state='TEST2')
    endpoint3 = endPoint.EndPoint(test_data, state='TEST1', next_state='TEST2')
    assert 'state: NONE, next_state: NONE, data: ' in endpoint0.to_str()
    assert 'state: TEST1, next_state: NONE, data: ' in endpoint1.to_str()
    assert 'state: NONE, next_state: TEST2, data: ' in endpoint2.to_str()
    assert 'state: TEST1, next_state: TEST2, data: ' in endpoint3.to_str()


def test_endpoint_state_default():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint1.update_state('UNKNOWN')
    endpoint1.update_state()

    assert endpoint1.state == 'UNKNOWN' and endpoint1.next_state == 'NONE'
