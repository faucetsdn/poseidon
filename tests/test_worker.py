# -*- coding: utf-8 -*-
"""
Created on 31 Dec 2019
@author: cglewis
"""
import os

from workers.worker import callback
from workers.worker import load_workers
from workers.worker import main
from workers.worker import setup_docker
from workers.worker import setup_redis


def test_setup_docker():
    d = setup_docker()


def test_load_workers():
    os.system('cp workers/workers.json workers.json')
    workers = load_workers()


def test_setup_redis():
    r = setup_redis()


def test_callback():
    class MockChannel:
        def basic_ack(self, delivery_tag=None): return True

    class MockMethod:
        def __init__(self):
            self.delivery_tag = None
            self.routing_key = ''

    ch = MockChannel()
    method = MockMethod()
    body = "{'id': '', 'type': 'metadata', 'file_path': '/files/tcprewrite-dot1q-2019-12-31-17_33_32.961111-UTC/pcap-node-splitter-2019-12-31-17_34_17.314910-UTC/clients/trace_5c7820e51dbabbf0476097dda838c7eabfa8e160_2019-12-31_17_18_17-client-ip-38-103-36-98-192-168-0-46-38-103-36-98-eth-udpencap-ip-frame-wsshort-udp-esp-port-4500.pcap', 'data': '', 'results': {'tool': 'p0f', 'version': '0.1.7'}}"
    body = body.encode('utf-8')
    os.environ['VOL_PREFIX'] = '/tmp'
    callback(ch, method, None, body)
