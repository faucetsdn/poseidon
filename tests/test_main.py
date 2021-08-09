# -*- coding: utf-8 -*-
"""
Test module for poseidon.py

Created on 28 June 2016
@author: Charlie Lewis, dgrossman, MShel
"""
import json
import logging
import queue
import time

import schedule
from faucetconfgetsetter import FaucetLocalConfGetSetter
from faucetconfgetsetter import get_sdn_connect
from faucetconfgetsetter import get_test_config
from poseidon_core.constants import NO_DATA
from poseidon_core.controllers.sdnconnect import SDNConnect
from poseidon_core.controllers.sdnevents import SDNEvents
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.helpers.metadata import DNSResolver
from poseidon_core.helpers.prometheus import Prometheus
from poseidon_core.helpers.rabbit import Rabbit
from poseidon_core.operations.monitor import Monitor
from prometheus_client import REGISTRY

logger = logging.getLogger('test')

# initialize here since prometheus keeps a global registry
prom = Prometheus()
prom.initialize_metrics()


def test_rdns():
    resolver = DNSResolver()
    for _ in range(3):
        res = resolver.resolve_ips({'8.8.8.8', '8.8.4.4', '1.1.1.1'})
        for name in res.values():
            assert name != NO_DATA


def test_mirror_endpoint():
    s = get_sdn_connect(logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.mirror_endpoint(endpoint)


def test_unmirror_endpoint():
    s = get_sdn_connect(logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.operate()
    s.endpoints[endpoint.name] = endpoint
    s.unmirror_endpoint(endpoint)


def test_clear_filters():
    s = get_sdn_connect(logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.clear_filters()
    s = get_sdn_connect(logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.clear_filters()


def test_check_endpoints():
    s = get_sdn_connect(logger)
    s.sdnc = None
    s.check_endpoints([])


def test_endpoint_by_name():
    s = get_sdn_connect(logger)
    endpoint = s.endpoint_by_name('foo')
    assert endpoint == None
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoint_by_name('foo')
    assert endpoint == endpoint2


def test_endpoint_by_hash():
    s = get_sdn_connect(logger)
    endpoint = s.endpoint_by_hash('foo')
    assert endpoint == None
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoint_by_hash('foo')
    assert endpoint == endpoint2


def test_endpoints_by_ip():
    s = get_sdn_connect(logger)
    endpoints = s.endpoints_by_ip('10.0.0.1')
    assert endpoints == []
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '10.0.0.1', 'ipv6': 'None'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoints_by_ip('10.0.0.1')
    assert [endpoint] == endpoint2


def test_endpoints_by_mac():
    s = get_sdn_connect(logger)
    endpoints = s.endpoints_by_mac('00:00:00:00:00:01')
    assert endpoints == []
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoints_by_mac('00:00:00:00:00:00')
    assert [endpoint] == endpoint2


def test_get_q_item():

    class MockMQueue:

        def get_nowait(self):
            return 'Item'

        def task_done(self):
            return

    sdne = SDNEvents(logger, prom, get_sdn_connect(logger))
    m_queue = MockMQueue()
    assert (True, 'Item') == sdne.get_q_item(m_queue)


def test_format_rabbit_message():
    sdne = SDNEvents(logger, prom, get_sdn_connect(logger))
    faucet_event = []
    remove_list = []

    data = {'id': '', 'type': 'metadata', 'file_path': '/files/foo.pcap', 'data': {'10.0.2.15': {'full_os': 'Windows NT kernel', 'short_os': 'Windows',
                                                                                                 'link': 'Ethernet or modem', 'raw_mtu': '1500', 'mac': '08:00:27:cc:3f:1b'}, 'results': {'tool': 'p0f', 'version': '0.11.17'}}}
    message = ('poseidon.algos.decider', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert not retval
    assert msg_valid

    data = {'id': '', 'type': 'metadata', 'file_path': '/files/foo', 'data': {'6b33db53faf33c77d694ecab2e3fefadc7dacc70': {'valid': True, 'pcap_labels': None, 'decisions': {'investigate': False}, 'classification': {'labels': ['Administrator workstation', 'Developer workstation', 'Active Directory controller'], 'confidences': [
        0.9955250173194201, 0.004474982679786006, 7.939512151303659e-13]}, 'timestamp': 1608179739.839953, 'source_ip': '208.50.77.134', 'source_mac': '00:1a:8c:15:f9:80'}, 'pcap': 'trace_foo.pcap'}, 'results': {'tool': 'networkml', 'version': '0.6.7.dev4'}}
    message = ('poseidon.algos.decider', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert not retval
    assert msg_valid

    data = dict({'Key1': 'Val1'})
    message = ('FAUCET.Event', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {'Key1': 'Val1'}
    assert msg_valid
    assert faucet_event == [{'Key1': 'Val1'}]

    message = (None, data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert not msg_valid

    data = dict({'foo': 'bar'})
    message = ('poseidon.action.ignore', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.clear.ignored', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.remove', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.remove.ignored', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    ip_data = dict({'10.0.0.1': ['rule1']})
    message = ('poseidon.action.update_acls', ip_data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    data = [('foo', 'unknown')]
    message = ('poseidon.action.change', data)
    retval, msg_valid = sdne.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid


def test_rabbit_callback():
    def mock_method(): return True
    mock_method.routing_key = 'test_routing_key'
    mock_method.delivery_tag = 'test_delivery_tag'

    # force mock_method coverage
    assert mock_method()

    class MockChannel:
        def basic_ack(self, delivery_tag): return True

    class MockQueue:
        item = None

        def qsize(self):
            return 1

        def put(self, item):
            self.item = item
            return True

        # used for testing to verify that we put right stuff there
        def get_item(self):
            return self.item

    mock_channel = MockChannel()
    mock_queue = MockQueue()
    sdne = SDNEvents(logger, prom, get_sdn_connect(logger))
    rabbit_callback = sdne.rabbit_callback

    rabbit_callback(
        mock_channel,
        mock_method,
        'properties',
        '{"body": 0}',
        mock_queue)
    assert mock_queue.get_item() == (mock_method.routing_key, {'body': 0})

    rabbit_callback(
        mock_channel,
        mock_method,
        'properties',
        '{"body": 0}',
        mock_queue)


def test_find_new_machines():
    s = get_sdn_connect(logger)
    machines = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1', 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2', 'ipv6': '0'},
                {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3', 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4', 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5', 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo6'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv6': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo7'}]
    s.find_new_machines(machines)


def test_Monitor_init():
    config = get_test_config()
    sdnc = SDNConnect(
        config, logger, prom, faucetconfgetsetter_cl=FaucetLocalConfGetSetter)
    sdne = SDNEvents(logger, prom, sdnc)
    monitor = Monitor(logger, config, schedule, sdne.job_queue, sdnc, prom)
    hosts = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2', 'ipv6': '0'},
             {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5', 'ipv6': '0'}]
    monitor.prom.update_metrics(hosts)
    sdne.update_prom_var_time('last_rabbitmq_routing_key_time', 'routing_key', 'foo')


def test_SDNConnect_init():
    get_sdn_connect(logger)


def unregister_metrics():
    for collector, _ in tuple(REGISTRY._collector_to_names.items()):
        REGISTRY.unregister(collector)


def test_process():
    from threading import Thread

    class MockMonitor(Monitor):

        def __init__(self):
            self.sdnc = get_sdn_connect(logger)
            self.logger = self.sdnc.logger
            self.config = self.sdnc.config
            self.sdnc.config['TYPE'] = 'None'
            self.sdnc.get_sdn_context()
            self.sdnc.config['TYPE'] = 'faucet'
            self.sdnc.get_sdn_context()
            self.job_queue = queue.Queue()
            self.prom = prom
            endpoint = endpoint_factory('foo')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            endpoint.operate()
            self.sdnc.endpoints[endpoint.name] = endpoint
            endpoint = endpoint_factory('foo2')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            endpoint.queue_next('operate')
            self.sdnc.endpoints[endpoint.name] = endpoint
            endpoint = endpoint_factory('foo3')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            self.sdnc.endpoints[endpoint.name] = endpoint
            self.results = 0

        def get_q_item(self, q, timeout=1):
            if not self.results:
                self.results += 1
                return (True, ('foo', {'data': {}}))
            return (False, None)

        def format_rabbit_message(self, item, faucet_event, remove_list):
            return ({'data': {}}, False)

    mock_monitor = MockMonitor()

    assert mock_monitor.sdnc.investigation_budget()
    assert mock_monitor.sdnc.coprocessing_budget()
    handlers = [
        mock_monitor.job_update_metrics,
        mock_monitor.job_reinvestigation_timeout,
        mock_monitor.job_recoprocess,
        mock_monitor.schedule_mirroring,
        mock_monitor.schedule_coprocessing]
    for handler in handlers:
        handler()

    def thread1():
        time.sleep(5)
        mock_monitor.running = False

    t1 = Thread(target=thread1)
    t1.start()
    # mock_monitor.process()
    t1.join()

    mock_monitor.sdnc.sdnc = None
    for handler in handlers:
        handler()


def test_show_endpoints():
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation']}}}, 'ipv4_addresses': {
        '0.0.0.0': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
    s = get_sdn_connect(logger)
    s.endpoints[endpoint.name] = endpoint
    s.show_endpoints('all')
    s.show_endpoints('state active')
    s.show_endpoints('state ignored')
    s.show_endpoints('state unknown')
    s.show_endpoints('os windows')
    s.show_endpoints('role developer-workstation')


def test_merge_machine():
    s = get_sdn_connect(logger)
    old_machine = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                   'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    new_machine = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                   'segment': 'foo', 'port': '1', 'ipv4': '', 'ipv6': ''}
    s.merge_machine_ip(old_machine, new_machine)
    assert old_machine['ipv4'] == new_machine['ipv4']
    assert new_machine['ipv6'] == new_machine['ipv6']
