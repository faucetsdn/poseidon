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


import pytest
import time

from dns_verify import DNSRecord
from dns_verify import verify_dns_record
from dns_verify import resolved_addresses


def test_dns_record_class():
    r = DNSRecord()
    r.add('a', .1)
    assert 'a' in r
    time.sleep(.1)
    assert 'a' not in r
    assert 'q' not in r

    i = DNSRecord()
    i.add('a', .25)
    i.add('b', .25)
    i.add('c', .25)
    for rec in i:
        assert rec in i
    time.sleep(.25)
    for rec in i:
        assert rec not in i


def test_dns_packet_validation():
    ch = "rabbitmq channel"
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
    verify_dns_record(ch, method, properties, body)
    assert '0.0.0.0' in resolved_addresses
    assert '70.80.90.100' in resolved_addresses
    assert '00:1408:10:195::2374' in resolved_addresses

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
    assert verify_dns_record(ch, method, properties, body) == "TODO: signaling packet of interest"
