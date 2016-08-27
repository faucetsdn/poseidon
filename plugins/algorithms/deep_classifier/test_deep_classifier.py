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
Created on 24 August 2016
@author: bradh41, tlanham

Test module for deep learning
package to classify pcap hex
headers.
"""
import pytest
import re

# eval tests
from eval_deep_classifier import load_model
from eval_deep_classifier import rabbit_init

# train tests
from train_deep_classifier import parse_data
from train_deep_classifier import parse_header


@pytest.mark.skip(reason='requires rabbitmq broker, integration test')
def test_rabbit_init():
    channel, connection = rabbit_init(host='poseidon-rabbit',
                                      exchange='topic-poseidon-internal',
                                      queue_name='poseidon.tcpdump_parser.#')


def test_load_model():
    assert load_model('not_a_file.abc') is None


def test_parse_header():
    ret_dict = parse_header(
        '2015-05-20 12:41:45.812393 IP 0.0.0.0 > 0.0.0.0: ESP(), length 184')
    assert isinstance(ret_dict, type({}))
    assert ret_dict['src_ip'] == '0.0.0.0'
    assert ret_dict['dest_ip'] == '0.0.0.0'

    ret_dict = parse_header(
        '2015-05-20 12:41:45.812393 IP 0.0.0.0.80 > 0.0.0.0.80: ESP(), length 184')
    assert ret_dict['src_ip'] == '0.0.0.0'
    assert ret_dict['dest_ip'] == '0.0.0.0'
    assert ret_dict['src_port'] == '80'
    assert ret_dict['dest_port'] == '80'

    ret_dict = parse_header(
        '2015-05-20 13:10:38.684973 IP 350.137.451.220.53 > 136.145.402.267.52573: 2560 1/0/0 CNAME . (68)')
    assert ret_dict['src_ip'] == '350.137.451.220'
    assert ret_dict['src_port'] == '53'
    assert ret_dict['dest_ip'] == '136.145.402.267'
    assert ret_dict['dest_port'] == '52573'

    ret_dict = parse_header(
        '2015-05-20 13:10:38.611239 NOTIP 350.137.451.220.53 > 136.145.402.267.1: 2816 4/0/0 CNAME . (116)')
    assert ret_dict['src_ip'] == '350.137.451.220'
    assert ret_dict['src_port'] == '53'
    assert ret_dict['dest_ip'] == '136.145.402.267'
    assert ret_dict['dest_port'] == '1'

    ret_dict = parse_header(
        '2015-05-20 13:10:53.740027 IP 350.137.451.220.53 > 136.145.402.267.505: 9846 2/0/0 AAAA 00:1408:10:195::2374, AAAA (99)')
    assert ret_dict['src_ip'] == '350.137.451.220'
    assert ret_dict['src_port'] == '53'
    assert ret_dict['dest_ip'] == '136.145.402.267'
    assert ret_dict['dest_port'] == '505'

    ret_dict = parse_header(
        '1989-01-01 00:00:00.123 IP6 a::b:c:d:e.90 > q::w:e:r:t.78 0* PTD 1 20')
    assert ret_dict['src_ip'] == 'a::b:c:d:e'
    assert ret_dict['src_port'] == '90'
    assert ret_dict['dest_ip'] == 'q::w:e:r:t'
    assert ret_dict['dest_port'] == '78'


def test_parse_data():
    ret_str = parse_data(
        '\t0x0080:  e04b 2935 564f 91db 5344 5460 9189 33d0', 0)
    assert isinstance(ret_str, type(''))
    hex_pattern = re.compile(r'[0-9a-fA-F]+')
    m = re.search(hex_pattern, ret_str)
    assert m

    ret_str = parse_data(
        '\t0x0070:  ac4b 2925 164f 916b 5244 5470 1189 3dd0', 10)
    assert isinstance(ret_str, type(''))
    hex_pattern = re.compile(r'[0-9a-fA-F]+')
    m = re.search(hex_pattern, ret_str)
    assert m
    assert ret_str == 'ac4b2925164f'
