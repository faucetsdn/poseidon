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

from prometheus_client import REGISTRY

from poseidon_core.constants import NO_DATA
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.helpers.metadata import DNSResolver
from poseidon_core.helpers.prometheus import Prometheus
from poseidon_core.helpers.rabbit import Rabbit
from poseidon_core.monitor import Monitor
from poseidon_core.sdnconnect import SDNConnect

logger = logging.getLogger('test')


def test_rdns():
    resolver = DNSResolver()
    for _ in range(3):
        res = resolver.resolve_ips({'8.8.8.8', '8.8.4.4', '1.1.1.1'})
        for name in res.values():
            if name != NO_DATA:
                return
    assert not res


def get_test_controller():
    controller = Config().get_config()
    controller['faucetconfrpc_address'] = None
    controller['TYPE'] = 'faucet'
    return controller


def test_mirror_endpoint():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.mirror_endpoint(endpoint)


def test_unmirror_endpoint():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    endpoint.operate()
    s.endpoints[endpoint.name] = endpoint
    s.unmirror_endpoint(endpoint)


def test_clear_filters():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.clear_filters()
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    s.clear_filters()


def test_check_endpoints():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    s.sdnc = None
    s.check_endpoints([])


def test_endpoint_by_name():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = s.endpoint_by_name('foo')
    assert endpoint == None
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoint_by_name('foo')
    assert endpoint == endpoint2


def test_endpoint_by_hash():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoint = s.endpoint_by_hash('foo')
    assert endpoint == None
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoint_by_hash('foo')
    assert endpoint == endpoint2


def test_endpoints_by_ip():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    endpoints = s.endpoints_by_ip('10.0.0.1')
    assert endpoints == []
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '10.0.0.1', 'ipv6': 'None'}
    s.endpoints[endpoint.name] = endpoint
    endpoint2 = s.endpoints_by_ip('10.0.0.1')
    assert [endpoint] == endpoint2


def test_endpoints_by_mac():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
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

        def task_done(self):
            return

        def get_nowait(self):
            return 'Item'

        def task_done(self):
            return

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = get_test_controller()
            self.s = SDNConnect(self.controller, logger)

    mock_monitor = MockMonitor()
    m_queue = MockMQueue()
    assert (True, 'Item') == mock_monitor.get_q_item(m_queue)


def test_format_rabbit_message():

    class MockLogger:

        def __init__(self):
            self.logger = logger

    class MockParser:

        def ignore_event(self, _):
            return False

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = get_test_controller()
            self.s = SDNConnect(self.controller, logger)
            self.s.sdnc = MockParser()

        def update_routing_key_time(self, routing_key):
            return

    mockMonitor = MockMonitor()
    mockMonitor.logger = MockLogger().logger
    faucet_event = []
    remove_list = []

    data = {"id": "", "type": "metadata", "file_path": "/files/foo.pcap", "data": {"10.0.2.15": {"full_os": "Windows NT kernel", "short_os": "Windows", "link": "Ethernet or modem", "raw_mtu": "1500", "mac": "08:00:27:cc:3f:1b"}, "results": {"tool": "p0f", "version": "0.11.17"}}}
    message = ('poseidon.algos.decider', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert not retval
    assert msg_valid

    data = {'id': '', 'type': 'metadata', 'file_path': '/files/foo', 'data': {'6b33db53faf33c77d694ecab2e3fefadc7dacc70': {'valid': True, 'pcap_labels': None, 'decisions': {'investigate': False}, 'classification': {'labels': ['Administrator workstation', 'Developer workstation', 'Active Directory controller'], 'confidences': [0.9955250173194201, 0.004474982679786006, 7.939512151303659e-13]}, 'timestamp': 1608179739.839953, 'source_ip': '208.50.77.134', 'source_mac': '00:1a:8c:15:f9:80'}, 'pcap': 'trace_foo.pcap'}, 'results': {'tool': 'networkml', 'version': '0.6.7.dev4'}}
    message = ('poseidon.algos.decider', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert not retval
    assert msg_valid

    data = dict({'Key1': 'Val1'})
    message = ('FAUCET.Event', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {'Key1': 'Val1'}
    assert msg_valid
    assert faucet_event == [{'Key1': 'Val1'}]

    message = (None, data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert not msg_valid

    data = dict({'foo': 'bar'})
    message = ('poseidon.action.ignore', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.clear.ignored', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.remove', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    message = ('poseidon.action.remove.ignored', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    ip_data = dict({'10.0.0.1': ['rule1']})
    message = ('poseidon.action.update_acls', ip_data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
        message, faucet_event, remove_list)
    assert retval == {}
    assert msg_valid

    data = [('foo', 'unknown')]
    message = ('poseidon.action.change', data)
    retval, msg_valid = mockMonitor.format_rabbit_message(
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

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = {'FA_RABBIT_ROUTING_KEY': mock_method.routing_key}
            self.s = None
            self.prom = None

    mock_channel = MockChannel()
    mock_queue = MockQueue()
    monitor = MockMonitor()
    rabbit_callback = monitor.rabbit_callback

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
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
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
    monitor = Monitor(logger, controller=get_test_controller())
    hosts = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2', 'ipv6': '0'},
             {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4', 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5', 'ipv6': '0'}]
    monitor.prom.update_metrics(hosts)
    monitor.update_routing_key_time('foo')


def test_SDNConnect_init():
    controller = get_test_controller()
    controller['trunk_ports'] = []
    SDNConnect(controller, logger)


def unregister_metrics():
    for collector, _ in tuple(REGISTRY._collector_to_names.items()):
        REGISTRY.unregister(collector)


def test_process():

    unregister_metrics()
    from threading import Thread

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = get_test_controller()
            self.s = SDNConnect(self.controller, logger)
            self.s.controller['TYPE'] = 'None'
            self.s.get_sdn_context()
            self.s.controller['TYPE'] = 'faucet'
            self.s.get_sdn_context()
            self.job_queue = queue.Queue()
            self.m_queue = queue.Queue()
            self.prom = Prometheus()
            self.prom.initialize_metrics()
            self.running = True
            endpoint = endpoint_factory('foo')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            endpoint.operate()
            self.s.endpoints[endpoint.name] = endpoint
            endpoint = endpoint_factory('foo2')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            endpoint.queue_next('operate')
            self.s.endpoints[endpoint.name] = endpoint
            endpoint = endpoint_factory('foo3')
            endpoint.endpoint_data = {
                'active': 0, 'ipv4_subnet': '12.12.12.12/24', 'ipv6_subnet': '', 'ipv4_rdns': '', 'ipv6_rdns': '', 'controller_type': 'faucet', 'controller': '', 'name': '', 'ipv4': '12.12.12.12', 'ipv6': '', 'ether_vendor': 'foo', 'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation', 'foo', 'bar'], 'confidences': [0.8, 0.2, 0.0]}}}, 'ipv4_addresses': {
                '12.12.12.12': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
            self.s.endpoints[endpoint.name] = endpoint
            self.results = 0

        def get_q_item(self, q, timeout=1):
            if not self.results:
                self.results += 1
                return (True, ('foo', {'data': {}}))
            return (False, None)

        def bad_get_q_item(self, q, timeout=1):
            return (False, ('bar', {'data': {}}))

        def format_rabbit_message(self, item, faucet_event, remove_list):
            return ({'data': {}}, False)

    mock_monitor = MockMonitor()

    assert mock_monitor.s.investigation_budget()
    assert mock_monitor.s.coprocessing_budget()
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
    mock_monitor.process()
    t1.join()

    mock_monitor.s.sdnc = None
    for handler in handlers:
        handler()


def test_show_endpoints():
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {
        'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    endpoint.metadata = {'mac_addresses': {'00:00:00:00:00:00': {'classification': {'labels': ['developer workstation']}}}, 'ipv4_addresses': {
        '0.0.0.0': {'os': 'windows'}}, 'ipv6_addresses': {'1212::1': {'os': 'windows'}}}
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    s.endpoints[endpoint.name] = endpoint
    s.show_endpoints('all')
    s.show_endpoints('state active')
    s.show_endpoints('state ignored')
    s.show_endpoints('state unknown')
    s.show_endpoints('os windows')
    s.show_endpoints('role developer-workstation')


def test_merge_machine():
    controller = get_test_controller()
    s = SDNConnect(controller, logger)
    old_machine = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                   'segment': 'foo', 'port': '1', 'ipv4': '0.0.0.0', 'ipv6': '1212::1'}
    new_machine = {'tenant': 'foo', 'mac': '00:00:00:00:00:00',
                   'segment': 'foo', 'port': '1', 'ipv4': '', 'ipv6': ''}
    s.merge_machine_ip(old_machine, new_machine)
    assert old_machine['ipv4'] == new_machine['ipv4']
    assert new_machine['ipv6'] == new_machine['ipv6']


def test_schedule_thread_worker():
    from threading import Thread

    class mockSchedule():

        def __init__(self):
            pass

        def run_pending(self):
            pass

    class mocksys():

        def __init__(self):
            pass

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = get_test_controller()
            self.s = SDNConnect(self.controller, logger)
            self.running = True

    mock_monitor = MockMonitor()

    def thread1():
        time.sleep(5)
        mock_monitor.running = False

    sys = mocksys()
    t1 = Thread(target=thread1)
    t1.start()
    try:
        mock_monitor.schedule_thread_worker(mockSchedule())
    except SystemExit:
        pass
    t1.join()
