# -*- coding: utf-8 -*-
"""
Test module for poseidon.py

Created on 28 June 2016
@author: Charlie Lewis, dgrossman, MShel
"""
import json
import logging
import os
import time

import redis
from prometheus_client import Gauge

from poseidon.helpers.config import Config
from poseidon.helpers.endpoint import Endpoint
from poseidon.main import CTRL_C
from poseidon.main import Monitor
from poseidon.main import rabbit_callback
from poseidon.main import schedule_job_kickurl
from poseidon.main import schedule_job_reinvestigation
from poseidon.main import schedule_thread_worker
from poseidon.main import SDNConnect

logger = logging.getLogger('test')


def test_endpoint_by_name():
    s = SDNConnect()
    endpoint = s.endpoint_by_name('foo')
    assert endpoint == None


def test_endpoint_by_hash():
    s = SDNConnect()
    endpoint = s.endpoint_by_hash('foo')
    assert endpoint == None


def test_endpoints_by_ip():
    s = SDNConnect()
    endpoints = s.endpoints_by_ip('10.0.0.1')
    assert endpoints == []


def test_endpoints_by_mac():
    s = SDNConnect()
    endpoints = s.endpoints_by_mac('00:00:00:00:00:01')
    assert endpoints == []


def test_signal_handler():

    class MockLogger:
        def __init__(self):
            self.logger = logger

    class MockRabbitConnection:
        connection_closed = False

        def close(self):
            self.connection_closed = True
            return True

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = Config().get_config()
            self.s = SDNConnect()

    class MockSchedule:
        call_log = []

        def __init__(self):
            self.jobs = ['job1', 'job2', 'job3']

        def cancel_job(self, job):
            self.call_log.append(job + ' cancelled')
            return job + ' cancelled'

    mock_monitor = MockMonitor()
    mock_monitor.schedule = MockSchedule()
    mock_monitor.rabbit_channel_connection_local = MockRabbitConnection()
    mock_monitor.logger = MockLogger().logger

    # signal handler seem to simply exit and kill all the jobs no matter what
    # we pass

    mock_monitor.signal_handler(None, None)
    assert ['job1 cancelled', 'job2 cancelled',
            'job3 cancelled'] == mock_monitor.schedule.call_log
    assert True == mock_monitor.rabbit_channel_connection_local.connection_closed


def test_get_q_item():
    class MockMQueue:

        def get(self, block):
            return 'Item'

        def task_done(self):
            return

    CTRL_C['STOP'] = False

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.controller = Config().get_config()
            self.s = SDNConnect()

    mock_monitor = MockMonitor()
    mock_monitor.m_queue = MockMQueue()
    assert (True, 'Item') == mock_monitor.get_q_item()

    CTRL_C['STOP'] = True
    mock_monitor.m_queue = MockMQueue()
    assert (False, None) == mock_monitor.get_q_item()


def test_format_rabbit_message():
    CTRL_C['STOP'] = False

    class MockLogger:
        def __init__(self):
            self.logger = logger

    class MockMonitor(Monitor):

        def __init__(self):
            self.fa_rabbit_routing_key = 'foo'
            self.logger = logger
            self.controller = Config().get_config()
            self.s = SDNConnect()

    mockMonitor = MockMonitor()
    mockMonitor.logger = MockLogger().logger

    data = dict({'Key1': 'Val1'})
    message = ('poseidon.algos.decider', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == data

    message = ('FAUCET.Event', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == data

    message = (None, json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    data = dict({'foo': 'bar'})
    message = ('poseidon.action.ignore', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    message = ('poseidon.action.clear.ignored', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    message = ('poseidon.action.change', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    message = ('poseidon.action.remove', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    message = ('poseidon.action.remove.ignored', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}

    message = ('poseidon.action.remove.inactives', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)
    assert retval == {}


def test_rabbit_callback():
    def mock_method(): return True
    mock_method.routing_key = 'test_routing_key'

    # force mock_method coverage
    assert mock_method()

    class MockQueue:
        item = None

        def put(self, item):
            self.item = item
            return True

        # used for testing to verify that we put right stuff there
        def get_item(self):
            return self.item

    mock_queue = MockQueue()
    rabbit_callback(
        'Channel',
        mock_method,
        'properties',
        'body',
        mock_queue)
    assert mock_queue.get_item() == (mock_method.routing_key, 'body')

    rabbit_callback(
        'Channel',
        mock_method,
        'properties',
        'body',
        None)


def test_schedule_job_kickurl():

    class func():

        def __init__(self):
            self.logger = logger
            self.faucet_event = []
            self.s = SDNConnect()

    schedule_job_kickurl(func())


def test_schedule_job_reinvestigation():

    class func():

        def __init__(self):
            self.logger = logger
            self.faucet_event = []
            self.controller = Config().get_config()
            self.controller['max_concurrent_reinvestigations'] = 10
            self.s = SDNConnect()
            if 'POSEIDON_TRAVIS' in os.environ:
                self.s.r = redis.StrictRedis(host='localhost',
                                             port=6379,
                                             db=0,
                                             decode_responses=True)
            endpoint = Endpoint('foo')
            endpoint.endpoint_data = {
                'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.mirror()
            endpoint.known()
            self.s.endpoints.append(endpoint)
            endpoint = Endpoint('foo2')
            endpoint.endpoint_data = {
                'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.mirror()
            endpoint.known()
            self.s.endpoints.append(endpoint)
            self.s.store_endpoints()
            self.s.get_stored_endpoints()

    schedule_job_reinvestigation(func())


def test_find_new_machines():
    s = SDNConnect()
    machines = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1', 'behavior': 1, 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2', 'behavior': 1, 'ipv6': '0'},
                {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                    'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3', 'behavior': 1, 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4', 'behavior': 1, 'ipv6': '0'},
                {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5', 'behavior': 1, 'ipv6': '0'}]
    s.find_new_machines(machines)


def test_Monitor_init():
    monitor = Monitor(skip_rabbit=True)
    hosts = [{'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo1', 'behavior': 1, 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo2', 'behavior': 1, 'ipv6': '0'},
             {'active': 0, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 1, 'segment': 'switch1', 'ipv4': '123.123.123.123', 'mac': '00:00:00:00:00:00', 'id': 'foo3', 'behavior': 1, 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon1', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1',
                 'port': 2, 'segment': 'switch1', 'ipv4': '2106::1', 'mac': '00:00:00:00:00:00', 'id': 'foo4', 'behavior': 1, 'ipv6': '0'},
             {'active': 1, 'source': 'poseidon', 'role': 'unknown', 'state': 'unknown', 'ipv4_os': 'unknown', 'tenant': 'vlan1', 'port': 1, 'segment': 'switch1', 'ipv4': '::', 'mac': '00:00:00:00:00:00', 'id': 'foo5', 'behavior': 1, 'ipv6': '0'}]
    monitor.prom.update_metrics(hosts)


def test_process():
    from threading import Thread

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        time.sleep(5)
        CTRL_C['STOP'] = True

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = logger
            self.fa_rabbit_routing_key = 'FAUCET.Event'
            self.faucet_event = None
            self.controller = Config().get_config()
            self.s = SDNConnect()
            self.s.controller['TYPE'] = 'bcf'
            self.s.get_sdn_context()
            self.s.controller['TYPE'] = 'faucet'
            self.s.get_sdn_context()
            if 'POSEIDON_TRAVIS' in os.environ:
                self.s.r = redis.StrictRedis(host='localhost',
                                             port=6379,
                                             db=0,
                                             decode_responses=True)
            endpoint = Endpoint('foo')
            endpoint.endpoint_data = {
                'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.mirror()
            endpoint.p_prev_states.append(
                (endpoint.state, int(time.time())))
            self.s.endpoints.append(endpoint)
            endpoint = Endpoint('foo2')
            endpoint.endpoint_data = {
                'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            endpoint.p_next_state = 'mirror'
            endpoint.queue()
            endpoint.p_prev_states.append(
                (endpoint.state, int(time.time())))
            self.s.endpoints.append(endpoint)
            endpoint = Endpoint('foo3')
            endpoint.endpoint_data = {
                'tenant': 'foo', 'mac': '00:00:00:00:00:00', 'segment': 'foo', 'port': '1'}
            self.s.endpoints.append(endpoint)
            self.s.store_endpoints()
            self.s.get_stored_endpoints()

        def get_q_item(self):
            return (True, ('foo', {}))

        def bad_get_q_item(self):
            return (False, ('bar', {}))

        def format_rabbit_message(self, item):
            return {}

    mock_monitor = MockMonitor()

    t1 = Thread(target=thread1)
    t1.start()
    mock_monitor.process()

    t1.join()

    mock_monitor.get_q_item = mock_monitor.bad_get_q_item

    t1 = Thread(target=thread1)
    t1.start()
    mock_monitor.process()

    t1.join()


def test_schedule_thread_worker():
    from threading import Thread

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        time.sleep(5)
        CTRL_C['STOP'] = True

    class mockSchedule():

        def __init__(self):
            pass

        def run_pending(self):
            pass

    class mocksys():

        def __init__(self):
            pass

        # def exit(self):
        #    pass

    sys = mocksys()
    t1 = Thread(target=thread1)
    t1.start()
    try:
        schedule_thread_worker(mockSchedule())
    except SystemExit:
        pass

    t1.join()
