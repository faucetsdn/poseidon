# -*- coding: utf-8 -*-
"""
Test module for poseidon.py

Created on 28 June 2016
@author: Charlie Lewis, dgrossman, MShel
"""
import json

from prometheus_client import Gauge

from poseidon.helpers.config import Config
from poseidon.helpers.log import Logger
from poseidon.main import CTRL_C
from poseidon.main import Monitor
from poseidon.main import rabbit_callback
from poseidon.main import schedule_job_kickurl
from poseidon.main import schedule_job_reinvestigation
from poseidon.main import schedule_thread_worker
from poseidon.main import SDNConnect


def test_signal_handler():

    class MockLogger:
        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger

    class MockRabbitConnection:
        connection_closed = False

        def close(self):
            self.connection_closed = True
            return True

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger
            self.controller = Config().get_config()
            self.s = SDNConnect()

    class MockScheduele:
        call_log = []

        def __init__(self):
            self.jobs = ['job1', 'job2', 'job3']

        def cancel_job(self, job):
            self.call_log.append(job + ' cancelled')
            return job + ' cancelled'

    mock_monitor = MockMonitor()
    mock_monitor.schedule = MockScheduele()
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
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger
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
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger

    class MockMonitor(Monitor):

        def __init__(self):
            self.fa_rabbit_routing_key = 'foo'
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger
            self.controller = Config().get_config()
            self.s = SDNConnect()

    mockMonitor = MockMonitor()
    mockMonitor.logger = MockLogger().logger

    data = dict({'Key1': 'Val1'})
    message = ('poseidon.algos.decider', json.dumps(data))
    retval = mockMonitor.format_rabbit_message(message)

    assert retval == data

    message = (None, json.dumps(data))
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


def test_schedule_job_reinvestigation():

    class MockLogger:
        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger


def test_schedule_job_kickurl():

    class MockLogger():

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger

        def error(self, msg):
            pass

    class helper():

        def __init__(self):
            pass

        def update_endpoint_state(self, messages=None):
            pass

    class func():

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger
            self.faucet_event = []
            self.s = SDNConnect()

    schedule_job_kickurl(func())


def test_Monitor_init():
    monitor = Monitor(skip_rabbit=True)


def test_process():
    from threading import Thread
    import time

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        time.sleep(5)
        CTRL_C['STOP'] = True

    class MockLogger():

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger

    class MockMonitor(Monitor):

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger
            self.fa_rabbit_routing_key = 'FAUCET.Event'
            self.faucet_event = None
            self.controller = Config().get_config()
            self.s = SDNConnect()

        def get_q_item(self):
            return (True, ('foo', {}))

        def bad_get_q_item(self):
            return (False, ('bar', {}))

        def format_rabbit_message(self, item):
            return {}

        def start_vent_collector(self, endpoint_hash):
            return None

        def host_has_active_collectors(self, endpoint_hash):
            return False

    mock_monitor = MockMonitor()
    mock_monitor.logger = MockLogger().logger

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
    import time

    def thread1():
        global CTRL_C
        CTRL_C['STOP'] = False
        time.sleep(5)
        CTRL_C['STOP'] = True

    class MockLogger():

        def __init__(self):
            self.logger = Logger.logger
            self.poseidon_logger = Logger.poseidon_logger

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
        schedule_thread_worker(mockSchedule(), MockLogger().logger)
    except SystemExit:
        pass

    t1.join()
