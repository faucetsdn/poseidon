#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Test module for dns_verify.py

Created on 23 June 2016
@author: Travis Lanham
"""
import time

import pytest
from dns_verify import dns_records
from dns_verify import DNSRecord
from dns_verify import network_machines
from dns_verify import rabbit_init
from dns_verify import verify_dns_record


def test_dns_record_class():
    r = DNSRecord('a.b.c.d')
    assert r.name == 'a.b.c.d'
    r.add('a', .1)
    assert 'a' in r
    time.sleep(.1)
    assert 'a' not in r
    assert 'q' not in r

    i = DNSRecord('q.w.e.r')
    i.add('a', .25)
    i.add('b', .25)
    i.add('c', .25)
    for rec in i:
        assert rec in i
    time.sleep(.25)
    for rec in i:
        assert rec not in i


def test_dns_packet_validation():
    ch = 'rabbitmq channel'
    method = None
    properties = None
    body = """{'src_port' : '53',
                'raw_header': '1998-10-10 18:10:53.650447 IP 136.145.402.267.53 > 350.137.451.220.2: 42478 A 0.0.0.0, A 70.80.90.100, AAAA 00:1408:10:195::2374 (43)',
                'ethernet_type': 'IP',
                'src_ip': '136.145.402.267',
                'length': 0,
                'time': '18:10:53.650447',
                'date': '1998-10-10',
                'protocol': '42478',
                'dest_port': '2',
                'data': '3c111c2565390b6539303037b65370f',
                'dest_ip': '350.137.451.220',
                'dns_resolved': ['0.0.0.0', '70.80.90.100', '00:1408:10:195::2374']}"""

    network_machines.append('136.145.402.267')
    assert '136.145.402.267' not in dns_records
    verify_dns_record(ch, method, properties, body)
    assert '136.145.402.267' in dns_records
    assert '0.0.0.0' in dns_records['136.145.402.267'].resolved
    assert '70.80.90.100' in dns_records['136.145.402.267'].resolved
    assert '00:1408:10:195::2374' in dns_records['136.145.402.267'].resolved

    body = """{'src_port' : '1',
                'raw_header': '1998-10-10 18:10:53.650447 IP 136.145.402.267.1 > 350.137.451.220.80: Flags [.] ack abc, win def length 90',
                'ethernet_type': 'IP',
                'src_ip': '136.145.402.267',
                'length': 0,
                'time': '18:10:53.650447',
                'date': '1998-10-10',
                'protocol': 'Flags',
                'dest_port': '80',
                'data': '3c111c2565390b6539303037b65370f',
                'dest_ip': '350.137.451.220'}"""
    assert verify_dns_record(
        ch,
        method,
        properties,
        body) == 'TODO: signaling packet of interest'

    body = """{'src_port' : '53',
                'raw_header': '1998-10-10 18:10:53.650447 IP w.x.y.z.53 > 350.137.451.220.2: 42478 A 0.0.0.0, A 70.80.90.100, AAAA 00:1408:10:195::2374 (43)',
                'ethernet_type': 'IP',
                'src_ip': 'w.x.y.z',
                'length': 43,
                'time': '18:10:53.650447',
                'date': '1998-10-10',
                'protocol': '42478',
                'dest_port': '2',
                'data': '3c111c2565390b6539303037b65370f',
                'dest_ip': '350.137.451.220',
                'dns_resolved': ['0.0.0.0', '70.80.90.100', '00:1408:10:195::2374']}"""
    verify_dns_record(ch, method, properties, body)
    assert 'w.x.y.z' not in dns_records

    body = """{'src_port' : '53',
                'raw_header': '1998-10-10 18:10:53.650447 IP 136.145.402.267.53 > h.j.k.l.80: A 1.1.2.3 AAAA 5.8.13.21 (90)',
                'ethernet_type': 'IP',
                'src_ip': '136.145.402.267',
                'length': 90,
                'time': '18:10:53.650447',
                'date': '1998-10-10',
                'protocol': 'Flags',
                'dest_port': '80',
                'data': '3c111c2565390b6539303037b65370f',
                'dest_ip': 'h.j.k.l',
                'dns_resolved': ['1.1.2.3', '5.8.13.21']}"""
    verify_dns_record(ch, method, properties, body)
    assert '136.145.402.267' in dns_records
    assert '0.0.0.0' in dns_records['136.145.402.267'].resolved
    assert '70.80.90.100' in dns_records['136.145.402.267'].resolved
    assert '00:1408:10:195::2374' in dns_records['136.145.402.267'].resolved
    assert '1.1.2.3' in dns_records['136.145.402.267'].resolved
    assert '5.8.13.21' in dns_records['136.145.402.267'].resolved

    dns_records.clear()


@pytest.mark.skip(reason='requires rabbitmq broker, integration test')
def test_rabbit_init():
    channel, connection = rabbit_init(host='poseidon-rabbit',
                                      exchange='topic-poseidon-internal',
                                      queue_name='features_tcpdump')
