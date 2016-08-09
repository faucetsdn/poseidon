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
Test module for pcap_stats.py

Created on 23 June 2016
@author: lanhamt
"""
import pytest
from pcap_stats_utils import FlowRecord
from pcap_stats_utils import MachineNode
from pcap_stats_utils import TimeRecord
from pcap_stats import analyze_pcap
from pcap_stats import network_machines
import math


def test_time_record_class():
    t = TimeRecord()
    t.update_sent('2005-02-02 08:00:00.000000')
    t.update_sent('2005-02-02 08:00:01.000000')
    assert t.get_elapsed_time_sent() == 1000.0
    t.update_received('2006-03-01 02:00:00.000000')
    t.update_received('2006-03-01 02:00:02.000000')
    assert t.get_elapsed_time_received() == 2000.0


def test_machine_node_class():
    ip = '1.2.3.4'
    n = MachineNode(ip)
    assert n.num_packets_sent == 0

    n.add_pcap_record(50, 'a.b.c.google', False)
    assert n.num_packets_sent == 1
    assert n.num_packets_rec == 0
    assert n.get_mean_packet_len('sent') == 50.0

    n.add_pcap_record(30, 'a.b.c.google', True)
    assert n.num_packets_rec == 1
    assert n.get_mean_packet_len('rec') == 30.0

    for mac, freq in n.get_machines_sent_to():
        assert mac == 'a.b.c.google'
        assert freq == 1
    for mac, freq in n.get_machines_received_from():
        assert mac == 'a.b.c.google'
        assert freq == 1

    n.add_pcap_record(10, 'd.e.f.x', False)
    assert n.num_packets_sent == 2
    assert n.get_mean_packet_len('sent') == 30.0

    sent = {}
    for mac, freq in n.get_machines_sent_to():
        sent[mac] = freq
    assert sent['a.b.c.google'] == 1
    assert sent['d.e.f.x'] == 1

    n.add_pcap_record(10, 'a.b.c.google', True)
    assert n.num_packets_rec == 2
    assert n.get_mean_packet_len('rec') == 20.0
    for mac, freq in n.get_machines_received_from():
        assert mac == 'a.b.c.google'
        assert freq == 2


def test_flow_record_class():
    f = FlowRecord()
    assert isinstance(f.machines, dict)
    f.update('a.b.c.d', True, '99.88.77.66', False, 150, None)
    assert f.get_machine_node('a.b.c.d').num_packets_sent == 1
    assert f.get_machine_node('a.b.c.d').get_mean_packet_len('sent') == 150.0
    for mac, freq in f.machines['a.b.c.d'].get_machines_sent_to():
        assert mac == '99.88.77.66'
        assert freq == 1

    assert f.get_machine_node('99.88.77.66') is None

    f.update('204.63.227.78', True, 'a.b.c.d', True, 50, None)
    assert f.get_machine_node('a.b.c.d').num_packets_rec == 1
    assert f.get_machine_node('a.b.c.d').get_mean_packet_len('rec') == 50.0
    assert f.get_machine_node('204.63.227.78').num_packets_sent == 1
    assert f.get_machine_node('204.63.227.78').get_mean_packet_len('sent') == 50.0
    for mac, freq in f.get_machine_node(
            'a.b.c.d').get_machines_received_from():
        assert mac == '204.63.227.78'
        assert freq == 1

    f.update('a.b.c.d', True, '204.63.227.78', True, 30, None)
    assert f.get_machine_node('a.b.c.d').num_packets_sent == 2
    assert f.get_machine_node('a.b.c.d').get_mean_packet_len('sent') >= 76
    assert f.get_machine_node('204.63.227.78').num_packets_rec == 1
    assert f.get_machine_node('204.63.227.78').num_packets_sent == 1
    assert f.get_machine_node('204.63.227.78').get_mean_packet_len('rec') == 30.0

    abcd_sent = {}
    for mac, freq in f.get_machine_node('a.b.c.d').get_machines_sent_to():
        abcd_sent[mac] = freq
    assert abcd_sent['99.88.77.66'] == 1
    assert abcd_sent['204.63.227.78'] == 1
    abcd_rec = {}
    for mac, freq in f.get_machine_node(
            'a.b.c.d').get_machines_received_from():
        abcd_rec[mac] = freq
    assert abcd_rec['204.63.227.78'] == 1
    two_sent = {}
    for mac, freq in f.get_machine_node(
            '204.63.227.78').get_machines_sent_to():
        two_sent[mac] = freq
    assert two_sent['a.b.c.d'] == 1
    two_rec = {}
    for mac, freq in f.get_machine_node(
            '204.63.227.78').get_machines_received_from():
        two_rec[mac] = freq
    assert two_rec['a.b.c.d'] == 1


def test_analyze_pcap():
    ch = 'rabbitmq channel'
    method = None
    properties = None
    net_to_net = """{'src_port' : '53',
                    'raw_header': '1998-10-10 18:10:53.650447 IP 136.145.402.267.53 > 350.137.451.220.2: 42478 A 0.0.0.0, A 70.80.90.100, AAAA 00:1408:10:195::2374 (43)',
                    'ethernet_type': 'IP',
                    'src_ip': '136.145.402.267',
                    'length': 43,
                    'time': '18:10:53.650447',
                    'date': '1998-10-10',
                    'protocol': '42478',
                    'dest_port': '2',
                    'data': '3c111c2565390b6539303037b65370f',
                    'dest_ip': '350.137.451.220',
                    'dns_resolved': ['0.0.0.0', '70.80.90.100', '00:1408:10:195::2374']}"""

    net_to_out = """{'src_port' : '1',
                    'raw_header': '1998-10-10 18:10:53.650447 IP 136.145.402.267.1 > h.j.k.l.80: Flags [.] ack abc, win def length 90',
                    'ethernet_type': 'IP',
                    'src_ip': '136.145.402.267',
                    'length': 90,
                    'time': '18:10:53.650447',
                    'date': '1998-10-10',
                    'protocol': 'Flags',
                    'dest_port': '80',
                    'data': '3c111c2565390b6539303037b65370f',
                    'dest_ip': 'h.j.k.l'}"""

    out_to_net = """{'src_port': '2',
                    'dest_port': '42',
                    'src_ip': 'q.w.e.r',
                    'dest_ip': '24.56.78.90',
                    'time': '12:09:45.456789',
                    'date': '1992-11-02',
                    'protocol': 'Flags',
                    'data': '238746924700101001010001000d01010',
                    'length': 180,
                    'raw_header': '1992-11-02 12:09:45.456789 IP q.w.e.r.2 > 24.56.78.90.42: Flags [.] ack hi, syn 8sb2 length 180 GET'}"""

    out_to_out = """{'src_port': '2',
                    'dest_port': '42',
                    'src_ip': 'q.w.e.r',
                    'dest_ip': 'e.v.i.l',
                    'time': '12:09:45.456789',
                    'date': '1992-11-02',
                    'protocol': 'Flags',
                    'data': '238746924700101001010001000d01010',
                    'length': 20,
                    'raw_header': '1992-11-02 12:09:45.456789 IP q.w.e.r.2 > e.v.i.l.42: Flags [.] syn hi, ack 8sb2 length 20 POST'}"""

    network_machines.append('136.145.402.267')
    network_machines.append('24.56.78.90')
    network_machines.append('350.137.451.220')
    f = FlowRecord()

    analyze_pcap(ch, method, properties, net_to_net, f)
    assert isinstance(f.machines, dict)
    assert f.get_machine_node('136.145.402.267').num_packets_sent == 1
    assert f.get_machine_node('136.145.402.267').get_mean_packet_len('sent') == 43.0
    assert f.get_machine_node('136.145.402.267').get_packet_len_std_dev('rec') == 'Error retrieving standard deviation.'
    assert f.get_machine_node('350.137.451.220').num_packets_rec == 1
    assert f.get_machine_node('350.137.451.220').get_mean_packet_len('rec') == 43.0

    analyze_pcap(ch, method, properties, net_to_out, f)
    assert f.get_machine_node('h.j.k.l') is None
    assert f.get_machine_node('136.145.402.267').num_packets_sent == 2
    assert f.get_machine_node('136.145.402.267').get_mean_packet_len('sent') == 66.5
    stdev = f.get_machine_node('136.145.402.267').get_packet_len_std_dev('sent')
    assert math.floor(stdev) == 33
    assert f.get_machine_node('136.145.402.267').get_flow_duration('sent') == 0.0
    assert f.get_machine_node('350.137.451.220').get_flow_duration('received') == 0.0

    analyze_pcap(ch, method, properties, out_to_net, f)
    assert f.get_machine_node('q.w.e.r') is None
    assert f.get_machine_node('24.56.78.90').num_packets_rec == 1
    assert f.get_machine_node('24.56.78.90').get_mean_packet_len('rec') == 180.0

    one_sent = {}
    for mac, freq in f.get_machine_node(
            '136.145.402.267').get_machines_sent_to():
        one_sent[mac] = freq
    assert one_sent['350.137.451.220'] == 1
    assert one_sent['h.j.k.l'] == 1

    two_rec = {}
    for mac, freq in f.get_machine_node(
            '24.56.78.90').get_machines_received_from():
        two_rec[mac] = freq
    assert two_rec['q.w.e.r'] == 1

    three_rec = {}
    for mac, freq in f.get_machine_node(
            '350.137.451.220').get_machines_received_from():
        three_rec[mac] = freq
    assert three_rec['136.145.402.267'] == 1

    analyze_pcap(ch, method, properties, out_to_out, f)
