#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This example is a test of a usable API demonstrating the test and documentation
workflow for the code base.

Created on 17 May 2016
@author: Charlie Lewis, dgrossman
"""
import json
import logging
import logging.config
import Queue
import signal
import sys
import threading
import time
from functools import partial
from os import getenv

import requests
import schedule

from poseidon.baseClasses.Rabbit_Base import Rabbit_Base
from poseidon.poseidonMonitor.Config.Config import config_interface
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import \
    controller_interface

ENDPOINT_STATES = [('K', 'KNOWN'), ('U', 'UNKNOWN'), ('M', 'MIRRORING'),
                   ('S', 'SHUTDOWN'), ('R', 'REINVESTIGATING')]

module_logger = logging.getLogger(__name__)

CTRL_C = False


def schedule_job_kickurl(func, logger):
    logger.debug('kick')
    func.NorthBoundControllerAbstraction.get_endpoint(
        'Update_Switch_State').update_endpoint_state()


def rabbit_callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    module_logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        module_logger.debug('posedionMain workQueue is None')


def schedule_thread_worker(schedule, logger):
    global CTRL_C
    logLine = 'starting thread_worker'
    logger.debug(logLine)
    while not CTRL_C:
        schedule.run_pending()
        logLine = 'scheduler woke {0}'.format(
            threading.current_thread().getName())
        time.sleep(1)
        logger.debug(logLine)
    logger.debug('Threading stop:{0}'.format(
        threading.current_thread().getName()))


def start_investigating():
    pass


def schedule_job_reinvestigation(max_investigations, endpoints, logger):
    ostr = 'reinvestagtion time'
    logger.debug(ostr)
    logger.debug('endpoints:{0}'.format(endpoints))

    currently_investigating = 0
    for my_hash, my_value in endpoints.iteritems():
        if 'state' in my_value:
            if my_value['state'] == 'REINVESTIGATING':
                currently_investigating += 1

    if currently_investigating < max_investigations:
        ostr = 'room to investigate'
        logger.debug(ostr)
        for x in range(max_investigations - currently_investigating):
            ostr = 'starting investigation {0}'.format(x)
            logger.debug(ostr)
            start_investigating()
    else:
        ostr = 'investigators all busy'
        logger.debug(ostr)


class Monitor(object):

    def __init__(self, skip_rabbit):
        # get the logger setup
        self.logger = module_logger
        self.mod_configuration = dict()
        logging.basicConfig(level=logging.DEBUG)

        self.mod_name = self.__class__.__name__
        self.skip_rabbit = skip_rabbit

        # timer class to call things periodically in own thread
        self.schedule = schedule

        # rabbit
        self.rabbit_channel_local = None
        self.rabbit_chanel_connection_local = None
        self.rabbit_thread = None

        self.actions = dict()
        self.Config = config_interface
        self.Config.set_owner(self)
        self.NorthBoundControllerAbstraction = controller_interface
        self.NorthBoundControllerAbstraction.set_owner(self)

        # wire up handlers for Config
        self.logger.debug('handler Config')

        # check
        self.Config.configure()
        self.Config.first_run()
        self.Config.configure_endpoints()

        self.m_queue = Queue.Queue()

        # wire up handlers for NorthBoundControllerAbstraction
        self.logger.debug('handler NorthBoundControllerAbstraction')

        # check
        self.NorthBoundControllerAbstraction.configure()
        self.NorthBoundControllerAbstraction.first_run()
        self.NorthBoundControllerAbstraction.configure_endpoints()

        # make a shortcut
        self.uss = self.NorthBoundControllerAbstraction.get_endpoint(
            'Update_Switch_State')

        self.logger.debug('----------------------')
        self.configSelf()
        self.init_logging()

        scan_frequency = int(self.mod_configuration['scan_frequency'])
        self.schedule.every(scan_frequency).seconds.do(
            partial(schedule_job_kickurl, func=self, logger=self.logger))

        reinvestigation_frequency = int(
            self.mod_configuration['reinvestigation_frequency'])
        max_concurrent_reinvestigations = int(
            self.mod_configuration['max_concurrent_reinvestigations'])

        self.schedule.every(reinvestigation_frequency).seconds.do(
            partial(schedule_job_reinvestigation,
                    max_investigations=max_concurrent_reinvestigations,
                    endpoints=self.NorthBoundControllerAbstraction.get_endpoint(
                        'Update_Switch_State').endpoint_states,
                    logger=self.logger))

        self.schedule_thread = threading.Thread(
            target=partial(
                schedule_thread_worker,
                schedule=self.schedule,
                logger=self.logger),
            name='st_worker')

    def print_endpoint_state(self, endpoint_states):
        def same_old(logger, state, letter, endpoint_states):
            logger.debug('*******{0}*********'.format(state))

            out_flag = False
            for my_hash in endpoint_states.keys():
                my_dict = endpoint_states[my_hash]
                if my_dict['state'] == state:
                    out_flag = True
                    logger.debug('{0}:{1}:{2}'.format(
                        letter, my_hash, my_dict['endpoint']))
            if not out_flag:
                logger.debug('None')

        for l, s in ENDPOINT_STATES:
            same_old(self.logger, s, l, endpoint_states)

        self.logger.debug('****************')

    def init_logging(self):
        ''' setup logging  '''
        config = None

        path = getenv('loggingFile')

        if path is None:
            path = self.mod_configuration.get('loggingFile')

        if path is not None:
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def configSelf(self):
        ''' get configuraiton for this module '''
        conf = self.Config.get_endpoint('Handle_SectionConfig')
        for item in conf.direct_get(self.mod_name):
            k, v = item
            self.mod_configuration[k] = v
        ostr = '{0}:config:{1}'.format(self.mod_name, self.mod_configuration)
        self.logger.debug(ostr)

    def update_state(self, endpoint_states):
        ret_val = []
        next_state = None
        current_state = None
        for my_hash in endpoint_states.keys():
            my_dict = endpoint_states[my_hash]
            current_state = my_dict['state']
            if current_state == 'UNKNOWN':
                next_state = 'MIRRORING'
                ret_val.append((my_hash, current_state, next_state))
        return ret_val

    def start_vent_collector(self, dev_hash, num_captures=1):
        '''
        Given a device hash and optionally a number of captures
        to be taken, starts vent collector for that device with the
        options specified in poseidon.config.
        '''
        try:
            payload = {
                'nic': self.mod_configuration['collector_nic'],
                'id': dev_hash,
                'interval': self.mod_configuration['collector_interval'],
                'filter': '\'host {0}\''.format(
                    self.uss.get_endpoint_ip(dev_hash)),
                'iters': str(num_captures)}
            self.logger.debug('vent payload: ' + str(payload))
            vent_addr = self.mod_configuration[
                'vent_ip'] + ':' + self.mod_configuration['vent_port']
            uri = 'http://' + vent_addr + '/create'
            resp = requests.post(uri, json=payload)
            self.logger.debug('collector repsonse: ' + resp.text)
        except Exception as e:
            self.logger.debug('failed to start vent collector' + str(e))

    def process(self):
        global CTRL_C
        signal.signal(signal.SIGINT, partial(self.signal_handler))
        while not CTRL_C:
            self.logger.debug('***************CTRL_C:{0}'.format(CTRL_C))
            time.sleep(1)
            found_work, item = self.get_q_item()
            self.logger.debug('woke from sleeping')
            self.logger.debug('work:{0},item:{1}'.format(found_work, item))
            state_transitions = self.update_state(
                self.uss.return_endpoint_state())
            self.print_endpoint_state(self.uss.return_endpoint_state())
            for transition in state_transitions:
                my_hash, current_state, next_state = transition
                self.logger.debug(
                    'updating:{0}:{1}->{2}'.format(my_hash, current_state, next_state))
                if next_state == 'MIRRORING':
                    self.logger.debug('*********** NOTIFY VENT ***********')
                    self.start_vent_collector(my_hash)
                    self.logger.debug('*********** MIRROR PORT ***********')
                    self.uss.mirror_endpoint(my_hash)
                self.uss.change_endpoint_state(my_hash, next_state)

    def get_q_item(self):
        found_work = False
        item = None

        try:
            item = self.m_queue.get(False)
            found_work = True
        except Queue.Empty:
            pass

        return (found_work, item)

    def signal_handler(self, signal, frame):
        global CTRL_C
        CTRL_C = True
        self.logger.debug('=================CTRLC{0}'.format(CTRL_C))
        for job in self.schedule.jobs:
            self.logger.debug('CTRLC:{0}'.format(job))
            self.schedule.cancel_job(job)


def main(skip_rabbit=False):
    ''' main function '''
    pmain = Monitor(skip_rabbit=skip_rabbit)
    if not skip_rabbit:
        rabbit = Rabbit_Base()
        host = pmain.mod_configuration['rabbit-server']
        port = int(pmain.mod_configuration['rabbit-port'])
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
            'poseidon_main',
            pmain.m_queue)
        # def start_channel(self, channel, callback, queue):
        pmain.schedule_thread.start()

    # loop here until told not to
    pmain.process()

    pmain.logger.debug('SHUTTING DOWN')
    pmain.rabbit_channel_connection_local.close()
    pmain.rabbit_channel_local.close()
    pmain.logger.debug('EXITING')
    sys.exit(0)


if __name__ == '__main__':
    main(skip_rabbit=False)
