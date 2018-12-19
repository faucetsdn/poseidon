#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon, schedules the threads, connects to SDN
controllers and defines the Monitor class.

Created on 3 December 2018
@author: Charlie Lewis
"""
import ast
import json
import logging
import random
import signal
import sys
import threading
import time
from copy import deepcopy
from functools import partial

import queue
import requests
import schedule
from redis import StrictRedis

from poseidon.controllers.bcf.bcf import BcfProxy
from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.helpers.actions import Actions
from poseidon.helpers.config import Config
from poseidon.helpers.endpoint import Endpoint
from poseidon.helpers.endpoint import EndpointDecoder
from poseidon.helpers.log import Logger
from poseidon.helpers.prometheus import Prometheus
from poseidon.helpers.rabbit import Rabbit

requests.packages.urllib3.disable_warnings()

CTRL_C = dict()
CTRL_C['STOP'] = False
Logger()
logger = logging.getLogger('main')


def rabbit_callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    if q is not None:
        q.put((method.routing_key, body))
    else:
        logger.debug('posedionMain workQueue is None')


def schedule_job_kickurl(func):
    func.s.check_endpoints(messages=func.faucet_event)
    del func.faucet_event[:]

    try:
        # get current state
        req = requests.get(
            'http://poseidon-api:8000/v1/network_full', timeout=10)

        # send results to prometheus
        hosts = req.json()['dataset']
        func.prom.update_metrics(hosts)
    except Exception as e:  # pragma: no cover
        func.logger.error(
            'Unable to get current state and send it to Prometheus because: {0}'.format(str(e)))


def schedule_job_reinvestigation(func):
    ''' put endpoints into the reinvestigation state if possible '''
    candidates = []

    for endpoint in func.s.endpoints:
        if endpoint.state in ['queued', 'known', 'abnormal']:
            candidates.append(endpoint)

    # get random order of things that are known
    for _ in range(func.controller['max_concurrent_reinvestigations'] - func.s.investigations):
        if len(candidates) > 0:
            random.shuffle(candidates)
            chosen = candidates.pop()
            func.logger.info('Starting reinvestigation on: {0} {1}'.format(
                chosen.name, chosen.state))
            chosen.reinvestigate()
            func.s.investigations += 1
            chosen.p_prev_states.append(
                (endpoint.state, int(time.time())))
            Actions(chosen, func.s.sdnc).mirror_endpoint()


def schedule_thread_worker(schedule):
    ''' schedule thread, takes care of running processes in the future '''
    global CTRL_C
    logger.debug('Starting thread_worker')
    while not CTRL_C['STOP']:
        sys.stdout.flush()
        schedule.run_pending()
        time.sleep(1)
    logger.debug('Threading stop:{0}'.format(
        threading.current_thread().getName()))
    sys.exit()


class SDNConnect(object):

    def __init__(self):
        self.r = None
        self.first_time = True
        self.sdnc = None
        self.controller = Config().get_config()
        self.logger = logger
        self.get_sdn_context()
        self.endpoints = []
        self.investigations = 0

    def get_stored_endpoints(self):
        self.connect_redis()
        # load existing endpoints if any
        if self.r:
            try:
                p_endpoints = self.r.get('p_endpoints')
                if p_endpoints:
                    p_endpoints = ast.literal_eval(p_endpoints.decode('ascii'))
                    self.endpoints = []
                    for endpoint in p_endpoints:
                        self.endpoints.append(
                            EndpointDecoder(endpoint).get_endpoint())
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Unable to get existing endpoints from Redis because {0}'.format(str(e)))
        return

    def get_sdn_context(self):
        if 'TYPE' in self.controller and self.controller['TYPE'] == 'bcf':
            try:
                self.sdnc = BcfProxy(self.controller)
            except BaseException as e:  # pragma: no cover
                self.logger.error(
                    'BcfProxy could not connect to {0} because {1}'.format(
                        self.controller['URI'], e))
        elif 'TYPE' in self.controller and self.controller['TYPE'] == 'faucet':
            try:
                self.sdnc = FaucetProxy(self.controller)
            except BaseException as e:  # pragma: no cover
                self.logger.error(
                    'FaucetProxy could not connect to {0} because {1}'.format(
                        self.controller['URI'], e))
        else:
            self.logger.error(
                'Unknown SDN controller config: {0}'.format(
                    self.controller))

    def check_endpoints(self, messages=None):
        retval = {}
        retval['machines'] = None
        retval['resp'] = 'bad'

        current = None
        parsed = None

        try:
            current = self.sdnc.get_endpoints(messages=messages)
            parsed = self.sdnc.format_endpoints(current)
            retval['machines'] = parsed
            retval['resp'] = 'ok'
        except BaseException as e:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to {0} because {1}.'.format(
                    self.controller['URI'], e))
            retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.find_new_machines(parsed)

        return

    def connect_redis(self, host='redis', port=6379, db=0):
        self.r = None
        try:
            self.r = StrictRedis(host=host, port=port, db=db,
                                 socket_connect_timeout=2)
        except Exception as e:
            self.logger.error(
                'Failed connect to Redis because: {0}'.format(str(e)))
        return

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        for machine in machines:
            h = Endpoint.make_hash(machine)
            ep = None
            for endpoint in self.endpoints:
                if h == endpoint.name:
                    ep = endpoint
            if ep is not None and ep.endpoint_data != machine:
                self.logger.info(
                    'Endpoint changed: {0}:{1}'.format(h, machine))
                ep.endpoint_data = deepcopy(machine)
                if ep.state == 'inactive' and machine['active'] == 1:
                    if ep.p_next_state in ['known', 'abnormal']:
                        ep.trigger(ep.p_next_state)
                    else:
                        ep.unknown()
                    ep.p_prev_states.append((ep.state, int(time.time())))
                elif ep.state != 'inactive' and machine['active'] == 0:
                    if ep.state in ['mirroring', 'reinvestigating']:
                        self.investigations -= 1
                        if ep.state == 'mirroring':
                            ep.p_next_state = 'mirror'
                        elif ep.state == 'reinvestigating':
                            ep.p_next_state = 'reinvestigate'
                    ep.inactive()
                    ep.p_prev_states.append((ep.state, int(time.time())))
            elif ep is None:
                self.logger.info(
                    'Detected new endpoint: {0}:{1}'.format(h, machine))
                m = Endpoint(h)
                m.p_prev_states.append((m.state, int(time.time())))
                m.endpoint_data = deepcopy(machine)
                self.endpoints.append(m)

        self.store_endpoints()
        return

    def store_endpoints(self):
        # store latest version of endpoints in redis
        if self.r:
            try:
                serialized_endpoints = []
                for endpoint in self.endpoints:
                    serialized_endpoints.append(endpoint.encode())
                self.r.set('p_endpoints', str(serialized_endpoints))
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Unable to store endpoints in Redis because {0}'.format(str(e)))
        return


class Monitor(object):

    def __init__(self, skip_rabbit):
        self.faucet_event = []
        self.m_queue = queue.Queue()
        self.skip_rabbit = skip_rabbit
        self.logger = logger

        # get config options
        self.controller = Config().get_config()

        # timer class to call things periodically in own thread
        self.schedule = schedule

        # setup prometheus
        self.prom = Prometheus()
        try:
            self.prom.initialize_metrics()
        except Exception as e:  # pragma: no cover
            self.logger.debug(
                'Prometheus metrics are already initialized: {0}'.format(str(e)))
        Prometheus.start()

        # initialize sdnconnect
        self.s = SDNConnect()

        # retrieve endpoints from redis
        self.s.get_stored_endpoints()
        # set all retrieved endpoints to inactive at the start
        for endpoint in self.s.endpoints:
            if endpoint.state != 'inactive':
                if endpoint.state == 'mirroring':
                    endpoint.p_next_state = 'mirror'
                elif endpoint.state == 'reinvestigating':
                    endpoint.p_next_state = 'reinvestigate'
                elif endpoint.state == 'queued':
                    endpoint.p_next_state = 'queue'
                endpoint.endpoint_data['active'] = 0
                endpoint.inactive()
                endpoint.p_prev_states.append(
                    (endpoint.state, int(time.time())))

        # schedule periodic scan of endpoints thread
        self.schedule.every(self.controller['scan_frequency']).seconds.do(
            partial(schedule_job_kickurl, func=self))

        # schedule periodic reinvestigations thread
        self.schedule.every(self.controller['reinvestigation_frequency']).seconds.do(
            partial(schedule_job_reinvestigation, func=self))

        # schedule all threads
        self.schedule_thread = threading.Thread(
            target=partial(
                schedule_thread_worker,
                schedule=self.schedule),
            name='st_worker')

    def format_rabbit_message(self, item):
        ''' read a message off the rabbit_q
        the message should be item = (routing_key,msg)
        '''
        ret_val = {}

        routing_key, my_obj = item
        self.logger.debug('rabbit_message:{0}'.format(my_obj))
        # my_obj: (hash,data)
        my_obj = json.loads(my_obj)
        self.logger.debug('routing_key:{0}'.format(routing_key))
        if routing_key == 'poseidon.algos.decider':
            self.logger.debug('decider value:{0}'.format(my_obj))
            # TODO if valid response then send along otherwise nothing
            for key in my_obj:
                ret_val[key] = my_obj[key]
        elif routing_key == self.controller['FA_RABBIT_ROUTING_KEY']:
            self.logger.debug('FAUCET Event:{0}'.format(my_obj))
            for key in my_obj:
                ret_val[key] = my_obj[key]
        return ret_val

    def process(self):
        global CTRL_C
        signal.signal(signal.SIGINT, partial(self.signal_handler))
        while not CTRL_C['STOP']:
            time.sleep(1)
            found_work, item = self.get_q_item()
            ml_returns = {}

            if found_work and item[0] != self.controller['FA_RABBIT_ROUTING_KEY']:
                ml_returns = self.format_rabbit_message(item)
                self.logger.info(
                    'ML results: {0}'.format(ml_returns))
                # this can trigger change out of mirroring/reinvestigating
            elif found_work and item[0] == self.controller['FA_RABBIT_ROUTING_KEY']:
                self.faucet_event.append(self.format_rabbit_message(item))
                self.logger.debug(
                    'Faucet event: {0}'.format(self.faucet_event))

            for endpoint in self.s.endpoints:
                if endpoint.state == 'queued':
                    if self.s.investigations < self.controller['max_concurrent_reinvestigations']:
                        self.s.investigations += 1
                        endpoint.trigger(endpoint.p_next_state)
                        endpoint.p_next_state = None
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                        Actions(endpoint, self.s.sdnc).mirror_endpoint()
                elif endpoint.state == 'unknown':
                    # move to mirroring state
                    if self.s.investigations < self.controller['max_concurrent_reinvestigations']:
                        self.s.investigations += 1
                        endpoint.mirror()
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                        Actions(endpoint, self.s.sdnc).mirror_endpoint()
                    else:
                        endpoint.p_next_state = 'mirror'
                        endpoint.queue()
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                elif endpoint.state in ['mirroring', 'reinvestigating']:
                    if endpoint.name in ml_returns:
                        Actions(endpoint, self.s.sdnc).unmirror_endpoint()
                        self.logger.info('ml_valid type: {0}'.format(
                            type(ml_returns[endpoint.name]['valid'])))
                        if 'valid' in ml_returns[endpoint.name] and ml_returns[endpoint.name]['valid']:
                            ml_decision = None
                            if 'decisions' in ml_returns[endpoint.name] and 'behavior' in ml_returns[endpoint.name]['decisions']:
                                ml_decision = ml_returns[endpoint.name]['decisions']['behavior']
                            if ml_decision == 'normal':
                                endpoint.known()
                            else:
                                endpoint.abnormal()
                        else:
                            endpoint.unknown()
                        self.s.investigations -= 1
                        endpoint.p_prev_states.append(
                            (endpoint.state, int(time.time())))
                    else:
                        cur_time = int(time.time())
                        # timeout after 2 times the reinvestigation frequency
                        # in case something didn't report back, put back in an
                        # unknown state
                        if cur_time - endpoint.p_prev_states[-1][1] > 2*self.controller['reinvestigation_frequency']:
                            Actions(endpoint, self.s.sdnc).unmirror_endpoint()
                            endpoint.unknown()
                            self.s.investigations -= 1
                            endpoint.p_prev_states.append(
                                (endpoint.state, int(time.time())))

    def get_q_item(self):
        '''
        attempt to get a work item from the queue
        m_queue -> (routing_key, body)
        a read from get_q_item should be of the form
        (boolean,(routing_key, body))
        '''
        found_work = False
        item = None
        global CTRL_C

        if not CTRL_C['STOP']:
            try:
                item = self.m_queue.get(False)
                found_work = True
                self.m_queue.task_done()
            except queue.Empty:  # pragma: no cover
                pass

        return (found_work, item)

    def signal_handler(self, signal, frame):
        ''' hopefully eat a CTRL_C and signal system shutdown '''
        global CTRL_C
        CTRL_C['STOP'] = True
        self.logger.debug('=================CTRLC{0}'.format(CTRL_C))
        try:
            for job in self.schedule.jobs:
                self.logger.debug('CTRLC:{0}'.format(job))
                self.schedule.cancel_job(job)
            self.rabbit_channel_connection_local.close()
            self.rabbit_channel_connection_local_fa.close()
            sys.exit()
        except BaseException:  # pragma: no cover
            pass


def main(skip_rabbit=False):  # pragma: no cover
    # setup rabbit and monitoring of the network
    pmain = Monitor(skip_rabbit=skip_rabbit)
    if not skip_rabbit:
        rabbit = Rabbit()
        host = pmain.controller['rabbit_server']
        port = int(pmain.controller['rabbit_port'])
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_main'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    if pmain.controller['FA_RABBIT_ENABLED']:
        rabbit = Rabbit()
        host = pmain.controller['FA_RABBIT_HOST']
        port = pmain.controller['FA_RABBIT_PORT']
        exchange = pmain.controller['FA_RABBIT_EXCHANGE']
        queue_name = 'poseidon_main'
        binding_key = [pmain.controller['FA_RABBIT_ROUTING_KEY']+'.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local_fa = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    pmain.schedule_thread.start()

    # loop here until told not to
    pmain.process()

    pmain.logger.debug('SHUTTING DOWN')
    pmain.logger.debug('EXITING')
    sys.exit(0)


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
