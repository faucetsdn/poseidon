"""
Created on 2 October 2017
@author: Jorissss
"""
import pytest

from poseidon.poseidonMonitor import endPoint

test_data = {'tenant': u'FLOORPLATE',
             'mac': u'de:ad:be:ef:7f:12',
             'segment': u'prod',
             'name': None,
             'ip-address': u'102.179.20.100'}

def test_endpoint_creation():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint2 = endPoint.EndPoint.from_json(endpoint1.to_json())
    assert endpoint1.to_str() == endpoint2.to_str()

def test_endpoint_state_default():
    endpoint1 = endPoint.EndPoint(test_data)
    endpoint1.update_state('UNKNOWN')
    endpoint1.update_state()
    assert endpoint1.state == 'UNKNOWN' and endpoint1.next_state == 'NONE'
