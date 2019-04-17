# -*- coding: utf-8 -*-
"""
Created on 14 Jan 2019
@author: Charlie Lewis
"""
from poseidon.cli.cli import GetData
from poseidon.cli.cli import Parser
from poseidon.cli.cli import PoseidonShell
from poseidon.helpers.endpoint import Endpoint


def test_poseidonshell():
    shell = PoseidonShell()
    shell.do_record('foo.txt')
    shell.do_record('')
    shell.do_help('foo')
    shell.do_help('')
    shell.do_show('foo')
    shell.do_show('all')
    shell.do_show('history 10')
    shell.do_show('history')
    shell.do_show('role')
    shell.do_show('role developer-workstation')
    shell.do_show('')
    shell.do_task('foo')
    shell.do_task('')
    shell.do_task('clear')
    shell.do_task('clear 10')
    shell.do_quit('foo')
    shell.do_exit('foo')
    shell.do_playback('foo.txt')
    shell.do_playback('')
    shell.complete_show('foo', 'foo bar', 1, 1)
    shell.complete_task('foo', 'foo bar', 1, 1)
    shell.show_all('foo', [])
    shell.show_role('foo', [])
    shell.show_state('foo', [])
    shell.show_behavior('foo', [])
    shell.show_os('foo', [])
    shell.show_what('foo', [])
    shell.show_history('foo', [])
    shell.show_where('foo', [])
    shell.help_show()
    shell.show_authors('foo', [])
    shell.task_set('foo', [])
    shell.task_collect('foo', [])
    shell.task_ignore('foo', [])
    shell.task_clear('foo', [])
    shell.task_remove('foo', [])
    shell.task_remove('ignored', [])
    shell.task_remove('inactive', [])
    shell.help_task()
    shell.emptyline()
    shell.completenames('foo', 'foo', 1, 2)
    shell.completenames('eof', 'foo', 1, 2)
    shell.completenames('shell', 'foo', 1, 2)
    shell.do_shell('ls')
    shell.precmd('foo')
    shell.precmd('foo ?')
    shell.do_eof('foo')
    shell.close()
    foo = open('foo.txt', 'w')
    shell.file = foo
    shell.precmd('foo')


def test_check_flags():
    parser = Parser()
    fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = parser._check_flags({
                                                                                                                          'fields': 'all'}, '')
    assert fields == [
        'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4',
        'IPv4 Subnet', 'IPv6', 'IPv6 Subnet', 'Ethernet Vendor', 'Ignored',
        'State', 'Next State', 'First Seen', 'Last Seen',
        'Previous States', 'IPv4 OS\n(p0f)', 'IPv6 OS\n(p0f)', 'Previous IPv4 OSes\n(p0f)',
        'Previous IPv6 OSes\n(p0f)', 'Role\n(PoseidonML)', 'Role Confidence\n(PoseidonML)', 'Previous Roles\n(PoseidonML)',
        'Previous Role Confidences\n(PoseidonML)', 'Behavior\n(PoseidonML)', 'Previous Behaviors\n(PoseidonML)',
        'IPv4 rDNS', 'IPv6 rDNS', 'SDN Controller Type', 'SDN Controller URI'
    ]
    fields, sort_by, max_width, unique, nonzero, output_format, ipv4_only, ipv6_only, ipv4_and_ipv6 = parser._check_flags({
                                                                                                                          'fields': ['ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4'], 'sort_by': 1, 'max_width': 100, 'unique': True, 'nonzero': True, 'output_format': 'csv', '4': True, '6': True, '4and6': True}, '')
    assert fields == [
        'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4',
    ]
    assert sort_by == 1
    assert max_width == 100
    assert unique == True
    assert nonzero == True
    assert output_format == 'csv'
    assert ipv4_only == False
    assert ipv6_only == False
    assert ipv4_and_ipv6 == True


def test_display_results():
    parser = Parser()
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoints = [endpoint]
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4', 'IPv6'], ipv4_only=False, ipv6_only=True)
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv6'], ipv4_only=False, ipv4_and_ipv6=True)
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4'], ipv4_only=False, ipv4_and_ipv6=True)
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4'], ipv4_only=False, ipv4_and_ipv6=True, unique=True)
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4'], ipv4_only=False, ipv4_and_ipv6=True, nonzero=True)
    parser.display_results(endpoints, [
                           'ID', 'MAC Address', 'Switch', 'Port', 'VLAN', 'IPv4'], ipv4_only=False, ipv4_and_ipv6=True, nonzero=True, unique=True)


def test_get_flags():
    parser = Parser()
    flags, not_flags = parser.get_flags(
        'show all --fields=[id, mac] --sort_by=2 -4')
    assert flags == {'fields': ['id', 'mac'], 'sort_by': '2', '4': True}
    assert not_flags == 'show all'


def test_completion():
    parser = Parser()
    words = parser.completion(
        'this is a test', 'this is a test', ['this'])
    assert words == []


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


def test_get_controller():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'controller': 'foo'}
    controller = GetData._get_controller(endpoint)
    assert controller == 'foo'
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    controller = GetData._get_controller(endpoint)
    assert controller == 'NO DATA'


def test_get_controller_type():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'controller_type': 'foo'}
    controller_type = GetData._get_controller_type(endpoint)
    assert controller_type == 'foo'
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    controller_type = GetData._get_controller_type(endpoint)
    assert controller_type == 'NO DATA'


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
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0'}
    ipv4_subnet = GetData._get_ipv4_subnet(endpoint)
    assert ipv4_subnet == 'NO DATA'
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv4_subnet': '0.0.0.0/24'}
    ipv4_subnet = GetData._get_ipv4_subnet(endpoint)
    assert ipv4_subnet == '0.0.0.0/24'


def test_get_ipv6_subnet():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                              'segment': 'foo', 'port': '1', 'ipv6': '1212::1'}
    ipv6_subnet = GetData._get_ipv6_subnet(endpoint)
    assert ipv6_subnet == 'NO DATA'
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
    assert state == 'None'


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


def test_get_prev_states():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.p_prev_states = []
    prev_states = GetData._get_prev_states(endpoint)
    assert prev_states == 'NO DATA'
    endpoint.p_prev_states = [('unknown', 1551711125)]
    GetData._get_prev_states(endpoint)
    endpoint.p_prev_states = [('unknown', 1551711125), ('queued', 1551711126)]
    GetData._get_prev_states(endpoint)
    endpoint.p_prev_states = [('unknown', 1551711125), ('queued', 1551711126), (
        'queued', 1551711126), ('queued', 1551711827), ('queued', 1551811126)]
    GetData._get_prev_states(endpoint)


def test_get_ipv4_os():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0'}
    endpoint.metadata = {'ipv4_addresses': {}}
    ipv4_os = GetData._get_ipv4_os(endpoint)
    assert ipv4_os == 'NO DATA'
    endpoint.metadata = {'ipv4_addresses': {'0.0.0.0': {'os': 'foo'}}}
    ipv4_os = GetData._get_ipv4_os(endpoint)
    assert ipv4_os == 'foo'


def test_get_ipv6_os():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv6': '1212::1'}
    endpoint.metadata = {'ipv6_addresses': {}}
    ipv6_os = GetData._get_ipv6_os(endpoint)
    assert ipv6_os == 'NO DATA'
    endpoint.metadata = {'ipv6_addresses': {'1212::1': {'os': 'foo'}}}
    ipv6_os = GetData._get_ipv6_os(endpoint)
    assert ipv6_os == 'foo'


def test_get_role():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.metadata = {'mac_addresses': {}}
    role = GetData._get_role(endpoint)
    assert role == 'NO DATA'
    endpoint.metadata = {'mac_addresses': {
        '00:00:00:00:00:00': {'1551711125': {'labels': ['foo']}}}}
    role = GetData._get_role(endpoint)
    assert role == 'foo'


def test_get_role_confidence():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.metadata = {'mac_addresses': {}}
    confidence = GetData._get_role_confidence(endpoint)
    assert confidence == 'NO DATA'
    endpoint.metadata = {'mac_addresses': {
        '00:00:00:00:00:00': {'1551711125': {'confidences': [10.0]}}}}
    confidence = GetData._get_role_confidence(endpoint)
    assert confidence == '10.0'


def test_get_behavior():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.metadata = {'mac_addresses': {}}
    behavior = GetData._get_behavior(endpoint)
    assert behavior == 'NO DATA'
    endpoint.metadata = {'mac_addresses': {
        '00:00:00:00:00:00': {'1551711125': {'behavior': 'abnormal'}}}}
    behavior = GetData._get_behavior(endpoint)
    assert behavior == 'abnormal'


def test_get_prev_roles():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    GetData._get_prev_roles(endpoint)


def test_get_prev_role_confidences():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    GetData._get_prev_role_confidences(endpoint)


def test_get_prev_behaviors():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    GetData._get_prev_behaviors(endpoint)


def test_get_prev_ipv4_oses():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    GetData._get_prev_ipv4_oses(endpoint)


def test_get_prev_ipv6_oses():
    endpoint = Endpoint('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    GetData._get_prev_ipv6_oses(endpoint)
