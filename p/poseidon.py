#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon, controls the state machine and defines the
Monitor class.

Created on 3 December 2018
@author: Charlie Lewis
"""
import hashlib
import json
from functools import partial

import queue
import schedule

from p.controllers.bcf.bcf import BcfProxy
from p.controllers.faucet.faucet import FaucetProxy
from p.helpers.config import Config
from p.helpers.endpoint import Endpoint
from p.helpers.log import Logger
from p.helpers.prometheus import Prometheus
from p.helpers.rabbit import Rabbit


def rabbit_callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    Logger.poseidon_logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    if q is not None:
        q.put((method.routing_key, body))
    else:
        Logger.poseidon_logger.debug('posedionMain workQueue is None')


def schedule_job_kickurl(func, logger):
    pass


def schedule_job_reinvestigation(max_investigations, endpoints, logger):
    ''' put endpoints into the reinvestigation state if possible '''
    ostr = 'reinvestigation time'
    logger.debug(ostr)
    logger.debug('endpoints:{0}'.format(endpoints))
    candidates = []

    currently_investigating = 0
    currently_mirrored = 0
    for my_hash, my_value in endpoints.state.items():
        if my_value.state == 'REINVESTIGATING' or my_value.next_state == 'REINVESTIGATING':
            currently_investigating += 1
        if my_value.state == 'MIRRORING' or my_value.next_state == 'MIRRORING':
            currently_mirrored += 1
        elif my_value.state == 'KNOWN':
            candidates.append(my_hash)

    # get random order of things that are known
    random.shuffle(candidates)
    ostr = '{0} investigating & {1} mirroring'.format(
        currently_investigating, currently_mirrored)
    logger.debug(ostr)
    if currently_investigating + currently_mirrored <= max_investigations:
        ostr = 'room to investigate'
        logger.debug(ostr)
        for x in range(max_investigations - currently_investigating):
            if len(candidates) >= 1:
                chosen = candidates.pop()
                ostr = 'starting investigation {0}:{1}'.format(x, chosen)
                logger.debug(ostr)
                endpoints.state[chosen].next_state = 'REINVESTIGATING'
    else:
        ostr = 'investigators all busy'
        logger.debug(ostr)


def schedule_thread_worker(schedule, logger):
    ''' schedule thread, takes care of running processes in the future '''
    global CTRL_C
    logLine = 'starting thread_worker'
    logger.debug(logLine)
    while not CTRL_C['STOP']:
        sys.stdout.flush()
        schedule.run_pending()
        time.sleep(1)
    logger.debug('Threading stop:{0}'.format(
        threading.current_thread().getName()))
    sys.exit()


class SDNConnect(object):

    def __init__(self):
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.retval = {}
        self.first_time = True
        self.sdnc = None
        self.controller = Config().set_config()
        self.get_sdn_context()
        self.endpoints = []

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

    def check_endpoints(self):
        self.retval['machines'] = None
        self.retval['resp'] = 'bad'

        current = None
        parsed = None
        machines = {}

        try:
            current = self.sdnc.get_endpoints(messages=messages)
            parsed = self.sdnc.format_endpoints(current)
            machines = parsed
        except BaseException as e:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to {0} because {1}.'.format(
                    self.controller['URI'], e))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.poseidon_logger.debug('MACHINES:{0}'.format(machines))
        self.find_new_machines(machines)

        self.retval['machines'] = parsed
        self.retval['resp'] = 'ok'

        return json.dumps(self.retval)

    @staticmethod
    def make_hash(machine):
        ''' hash the unique metadata parts of an endpoint '''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        for word in ['tenant', 'mac', 'segment']:
            pre_h = pre_h + str(machine.get(word, 'missing'))
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        if self.first_time:
            self.first_time = False
            # db call to see if really need to run things
            # TODO - still not right
            if self.r:
                try:
                    mac_addresses = self.r.smembers('mac_addresses')
                    for mac in mac_addresses:
                        try:
                            mac_info = self.r.hgetall(mac)
                            if 'poseidon_hash' in mac_info:
                                try:
                                    poseidon_info = self.r.hgetall(
                                        mac_info['poseidon_hash'])
                                    if 'endpoint_data' in poseidon_info:
                                        endpoint_data = ast.literal_eval(
                                            poseidon_info['endpoint_data'])
                                        self.poseidon_logger.info(
                                            'adding address to known systems {0}'.format(endpoint_data))
                                        # endpoint_data seems to be incorrect
                                        #end_point = EndPoint(endpoint_data, state='KNOWN')
                                        # self.endpoints.set(end_point)
                                except Exception as e:  # pragma: no cover
                                    self.logger.error(
                                        'Unable to get endpoint data for {0} from Redis because {1}'.format(mac, str(e)))
                        except Exception as e:  # pragma: no cover
                            self.logger.error(
                                'Unable to get MAC information for {0} from Redis because {1}'.format(mac, str(e)))
                except Exception as e:  # pragma: no cover
                    self.logger.error(
                        'Unable to get existing DB information from Redis because {0}'.format(str(e)))
            for machine in machines:
                h = SDNConnect.make_hash()
                m = Endpoint(h)
                self.endpoints.append(m)
                self.poseidon_logger.info(
                    'Adding new endpoint {0}'.format(machine))
        else:
            for machine in machines:
                h = SDNConnect.make_hash()
                ep = None
                for endpoint in self.endpoints:
                    if h == endpoint.name:
                        ep = endpoint
                    if ep is not None and ep.endpoint_data != endpoint.endpoint_data:
                        self.poseidon_logger.info(
                            'Endpoint changed: {0}:{1}'.format(h, machine))
                        # TODO update the object in the self.endpoints array
                    elif ep is None and machine.endpoint_data['active'] == 1:
                        self.poseidon_logger.info(
                            'Detected new endpoint: {0}:{1}'.format(h, machine))
                        self.endpoints.append(machine)


class Monitor(object):

    def __init__(self, skip_rabbit):
        # get the logger setup
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.faucet_event = []
        self.m_queue = queue.Queue()
        self.skip_rabbit = skip_rabbit

        # timer class to call things periodically in own thread
        self.schedule = schedule

        m = Endpoint('foo')
        s = SDNConnect()
        Logger.set_level(s.controller['logger_level'])

        self.schedule.every(self.scan_frequency).seconds.do(
            partial(schedule_job_kickurl, func=self, logger=self.poseidon_logger))

        self.schedule.every(self.reinvestigation_frequency).seconds.do(
            partial(schedule_job_reinvestigation,
                    max_investigations=max_concurrent_reinvestigations,
                    endpoints=self.NorthBoundControllerAbstraction.get_endpoint(
                        'Update_Switch_State').endpoints,
                    logger=self.poseidon_logger))

        self.schedule_thread = threading.Thread(
            target=partial(
                schedule_thread_worker,
                schedule=self.schedule,
                logger=self.poseidon_logger),
            name='st_worker')


class Collector(object):

    def __init__(self, id, nic, interval, hash, iterations, host, status):
        self.id = id
        self.nic = nic
        self.interval = interval
        self.hash = hash
        self.iterations = iterations
        self.host = host
        self.status = status


def main(skip_rabbit=False):  # pragma: no cover
    # setup prometheus
    prom = Prometheus()
    prom.update_metrics()
    prom.start()

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

    if pmain.fa_rabbit_enabled:
        rabbit = Rabbit()
        host = pmain.controller['FA_RABBIT_HOST']
        port = pmain.controller['FA_RABBIT_PORT']
        exchange = pmain.controller['FA_RABBIT_EXCHANGE']
        queue_name = 'poseidon_main'
        binding_key = [pmain.controller['FA_RABBIT_ROUTING_KEY']+'.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    pmain.schedule_thread.start()

    # loop here until told not to
    pmain.process()

    pmain.poseidon_logger.debug('SHUTTING DOWN')
    pmain.poseidon_logger.debug('EXITING')
    sys.exit(0)


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
