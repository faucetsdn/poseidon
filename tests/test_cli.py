# -*- coding: utf-8 -*-
"""
Created on 14 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.cli import GetData
from poseidon.cli.cli import PoseidonShell
from poseidon.helpers.endpoint import Endpoint


def test_poseidonshell():
    shell = PoseidonShell()
    shell.do_record('foo.txt')
    shell.do_show('foo')
    shell.do_quit('foo')
    shell.do_playback('foo.txt')
    shell.precmd('foo')
    shell.close()


def test_get_name():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    name = GetData._get_name(endpoint)
    assert name == 'foo'


def test_get_mac():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    mac = GetData._get_mac(endpoint)
    assert mac == '00:00:00:00:00:00'


def test_get_switch():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    switch = GetData._get_switch(endpoint)
    assert switch == 'foo'


def test_get_port():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    port = GetData._get_port(endpoint)
    assert port == '1'


def test_get_vlan():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    vlan = GetData._get_vlan(endpoint)
    assert vlan == 'foo'


def test_get_ipv4():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0'}
    ipv4 = GetData._get_ipv4(endpoint)
    assert ipv4 == '0.0.0.0'


def test_get_ipv6():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv6': '1212::1'}
    ipv6 = GetData._get_ipv6(endpoint)
    assert ipv6 == '1212::1'


def test_get_ipv4_subnet():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv4_subnet = GetData._get_ipv4_subnet(endpoint)
    assert ipv4_subnet == '0.0.0.0/24'


def test_get_ipv6_subnet():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv6': '1212::1', 'ipv6_subnet': '1212::1/64'}
    ipv6_subnet = GetData._get_ipv6_subnet(endpoint)
    assert ipv6_subnet == '1212::1/64'


def test_get_ether_vendor():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ether_vendor = GetData._get_ether_vendor(endpoint)
    assert ether_vendor == 'NO DATA'
    endpoint.endpoint_data = {'ether_vendor': 'VENDOR', 'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ether_vendor = GetData._get_ether_vendor(endpoint)
    assert ether_vendor == 'VENDOR'


def test_get_ipv4_rdns():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv4_rdns = GetData._get_ipv4_rdns(endpoint)
    assert ipv4_rdns == 'NO DATA'
    endpoint.endpoint_data = {'ipv4_rdns': 'foo.internal', 'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv4_rdns = GetData._get_ipv4_rdns(endpoint)
    assert ipv4_rdns == 'foo.internal'


def test_get_ipv6_rdns():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv6_rdns = GetData._get_ipv6_rdns(endpoint)
    assert ipv6_rdns == 'NO DATA'
    endpoint.endpoint_data = {'ipv6_rdns': 'foo.internal', 'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv6_rdns = GetData._get_ipv6_rdns(endpoint)
    assert ipv6_rdns == 'foo.internal'


def test_get_ignored():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    ignored = GetData._get_ignored(endpoint)
    assert ignored == 'False'


def test_get_state():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    state = GetData._get_state(endpoint)
    assert state == 'unknown'


def test_get_next_state():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    state = GetData._get_next_state(endpoint)
    assert state == None


def test_get_first_seen():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.p_prev_states = [('unknown', 1551711125)]
    GetData._get_first_seen(endpoint)


def test_get_last_seen():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.p_prev_states = [('unknown', 1551711125)]
    GetData._get_last_seen(endpoint)
