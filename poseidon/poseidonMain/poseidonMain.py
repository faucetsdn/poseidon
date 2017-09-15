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
'''
poseidonMain

Created on 29 May 2016

@author: dgrossman, lanhamt

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue(in):  poseidon_main
        keys:   poseidon.algos.#,poseidon.action.#
'''
import json
import logging
import logging.config
import Queue
import threading
import time
import types
import urllib2
from collections import defaultdict
from functools import partial
from os import getenv

import requests

from poseidon.baseClasses.Rabbit_Base import Rabbit_Base
from poseidon.poseidonMain.Config.Config import config_interface
from poseidon.poseidonMain.Investigator.Investigator import \
    investigator_interface
from poseidon.poseidonMain.Scheduler.Scheduler import scheduler_interface

logging.basicConfig(level=logging.DEBUG)
module_logger = logging.getLogger(__name__)

ENDPOINT_STATES = [('K', 'KNOWN'), ('U', 'UNKNOWN'), ('M', 'MIRRORING'),
                   ('S', 'SHUTDOWN'), ('R', 'REINVESTIGATING')]


def callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    module_logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        module_logger.error('posedionMain workQueue is None')


def start_investigating():
    pass


def schedule_job_reinvestigation(max_investigations, endpoints, logger):
    ostr = 'reinvestagtion time'
    logger.info(ostr)

    currently_investigating = 0
    for my_hash, my_value in endpoints.iteritems():
        if 'state' in my_value:
            if my_value['state'] == 'REINVESTIGATION':
                currently_investigating += 1

    if currently_investigating < max_investigations:
        ostr = 'room to investigate'
        logger.info(ostr)
        for x in range(max_investigations - currently_investigating):
            ostr = 'starting investigation {0}'.format(x)
            logger.info(ostr)
            start_investigating()
    else:
        ostr = 'investigators all busy'
        logger.info(ostr)


def schedule_job_kickurl(url, logger):
    if url:
        try:
            page = urllib2.urlopen(url)
            logger.info(page.readlines())
            ostr = 'wget {0}'.format(url)
            logger.info(ostr)
        except BaseException:
            ostr = 'Error connecting to url: {0} retrying...'.format(url)
            logger.info(ostr)


class PoseidonMain(object):
    ''' poseidonmain '''

    def __init__(self, skip_rabbit=False):
        ''' poseidonMain initialization '''
        self.skip_rabbit = skip_rabbit

        self.rabbit_connection_local = None
        self.rabbit_channel_local = None

        self.rabbit_connection_vent = None
        self.rabbit_channel_vent = None

        self.logger = module_logger
        self.logger.debug('logger started')

        self.m_queue = Queue.Queue()
        self.shutdown_flag = False

        self.mod_configuration = dict()

        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name

        self.Investigator = investigator_interface
        self.Investigator.set_owner(self)

        self.Scheduler = scheduler_interface
        self.Scheduler.set_owner(self)

        self.Config = config_interface
        self.Config.set_owner(self)

        self.Config.configure()
        self.Config.configure_endpoints()

        self.Investigator.configure()
        self.Investigator.configure_endpoints()

        self.Scheduler.configure()
        self.Scheduler.configure_endpoints()

        self.endpoint_states = defaultdict(dict)

        # self.monitoring = {}
        # self.reinvestigation = {}
        # self.shutdown = {}

        for item in self.Config.get_section(self.config_section_name):
            my_k, my_v = item
            self.mod_configuration[my_k] = my_v

        self.init_logging()

        scan_frequency = int(self.mod_configuration['scan_frequency'])
        url = self.mod_configuration['scan_url']

        self.Scheduler.schedule.every(scan_frequency).seconds.do(
            partial(schedule_job_kickurl, url=url, logger=self.Scheduler.logger))

        reinvestigation_frequency = int(
            self.mod_configuration['reinvestigation_frequency'])
        max_concurrent_reinvestigations = int(
            self.mod_configuration['max_concurrent_reinvestigations'])
        self.Scheduler.schedule.every(reinvestigation_frequency).seconds.do(
            partial(schedule_job_reinvestigation, max_investigations=max_concurrent_reinvestigations, endpoints=self.endpoint_states, logger=self.Scheduler.logger))

    def init_logging(self):
        ''' setup the logging parameters for poseidon '''
        config = None

        path = getenv('loggingFile')

        if path is None:
            path = self.mod_configuration.get('loggingFile')

        if path is not None:
            with open(path, 'rt') as some_file:
                config = json.load(some_file)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    @staticmethod
    def make_type_val(item):
        ''' normalize messages '''
        endpoint = None
        value = None
        endpoint, value = item[0], item[1]

        return endpoint, value

    def make_endpoint_dict(self, hash, state, data):
        self.endpoint_states[hash]['state'] = state
        self.endpoint_states[hash]['endpoint'] = data

    def start_monitor(self, ivalue):
        ''' start monitoring an address'''
        self.logger.debug('start_monitor:{0},{1}'.format(ivalue, type(ivalue)))
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.start_monitor'
        r_msg = json.dumps(ivalue)

        for my_hash, my_value in ivalue.iteritems():

            # if my_hash not in monitoring:
            if my_hash not in self.endpoint_states:

                self.logger.debug(
                    'starting monitoring:{0}:{1}'.format(my_hash, my_value))

                # TODO MSG the collector to begin waiting. contents of my_value
                self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                        routing_key=r_key,
                                                        body=r_msg)

                make_endpoint_dict(my_hash, 'MONITORING', my_value)
                # self.monitoring[my_hash] = my_value

            else:
                # check to make sure that item is in the monitoring state
                if self.endpoint_states[my_hash]['state'] == 'MONITORING':
                    self.logger.debug(
                        'already being monitored:{0}:{1}'.format(
                            my_hash, my_value))
                else:
                    # endpoint was there for another reason, put into the monitoring state
                    # do the monitoring
                    update_state(my_hash, 'MONITORING')
                    self.logger.debug(
                        'starting monitoring:{0}:{1}'.format(my_hash, my_value))

                    self.endpoint_states[my_hash]['state'] = 'MONITORING'
                    self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                            routing_key=r_key,
                                                            body=r_msg)

    def update_state(self, my_hash, new_state):
        if my_hash in self.endpoint_states:
            old_state = self.endpoint_staes[my_hash]['state']
            self.logger.debug(
                'endpoint changing state:{0}:{1}'.format(old_state, new_state))
            self.endpoint_states[hash]['state'] = new_state

    def stop_monitor(self, ivalue):
        ''' stop monitoring an address'''

        for my_hash, my_dict in ivalue.iteritems():
            if my_hash in self.endpoint_states:
                update_state(my_hash, 'KNOWN')

        self.logger.debug('stop_monitor:{0},{1}'.format(ivalue, type(ivalue)))
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.stop_monitor'
        r_msg = json.dumps(ivalue)
        self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                routing_key=r_key,
                                                body=r_msg)

    def endpoint_shutdown(self, ivalue):
        ''' shutdown an endpoint '''
        self.logger.debug('endpoint_shutdown:{0}'.format(ivalue))
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.endpoint_shutdown'
        r_msg = json.dumps(ivalue)
        self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                routing_key=r_key,
                                                body=r_msg)

    def endpoint_allow(self, ivalue):
        ''' allow an endpoint '''
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.endpoint_allow'
        r_msg = json.dumps(ivalue)
        self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                routing_key=r_key,
                                                body=r_msg)

    def check_db(self, dev_hash, field):
        '''
        Given a device hash and field to look for in
        its record, queries the database for device record
        and returns the given field. Returns None on error.
        '''
        try:
            query = {'dev_id': dev_hash}
            query_string = str(query).replace("\'", "\"")
            ip = self.mod_configuration['storage_interface_ip']
            port = self.mod_configuration['storage_interface_port']
            uri = 'http://' + ip + ':' + port + \
                  '/v1/storage/query/{database}/{collection}/{query_str}'.format(
                      database=self.mod_configuration['database'],
                      collection=self.mod_configuration['collection'],
                      query_str=query_string)
            self.logger.error('check_db:{0}:{1}'.format(uri, type(uri)))
            resp = requests.get(uri)
            self.logger.debug('response from db:' + resp.text)

            # resp.text should load into dict 'docs' key for list of
            # documents matching the query - should be only 1 match
            resp = json.loads(resp.text)
            if resp['count'] == 1:
                db_doc = resp['docs'][0]
                self.logger.debug('found db doc: ' + str(db_doc))
                return db_doc[field]
            else:
                self.logger.debug('bad document in db: ' + str(db_doc))
        except Exception as e:
            self.logger.debug('failed to get record from db' + str(e))
            return None

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
                'filter': self.mod_configuration['collector_filter'],
                'iters': str(num_captures)}
            self.logger.debug('vent payload: ' + str(payload))
            vent_addr = self.mod_configuration[
                'vent_ip'] + ':' + self.mod_configuration['vent_port']
            uri = 'http://' + vent_addr + '/create'
            resp = requests.post(uri, json=payload)
            self.logger.debug('collector repsonse: ' + resp.text)
        except Exception as e:
            self.logger.debug('failed to start vent collector' + str(e))

    @staticmethod
    def just_the_hash(ivalue):
        return ivalue.keys()[0]

    def handle_item(self, itype, ivalue):
        self.logger.debug('handle_item:{0}:{1}'.format(itype, ivalue))

        # just get a string back from the ml stuff
        if 'poseidon.algos.eval_dev_class' not in itype:
            ivalue = json.loads(ivalue)

        if itype == 'poseidon.action.shutdown':
            self.logger.debug('***** shutting down')
            self.shutdown_flag = True
        if itype == 'poseidon.action.new_machine':
            self.logger.debug('***** new machine {0}'.format(ivalue))
            # tell monitor to monitor
            # dont remonitor something you are monitoring
            if self.just_the_hash(ivalue) not in self.endpoint_states:
                # didnt exist
                for my_hash, my_dict in ivalue.iteritems():
                    self.endpoint_states[my_hash]['state'] = 'MONITORING'
                    self.endpoint_states[my_hash]['endpoint'] = my_dict
                    self.start_vent_collector(self.just_the_hash(ivalue))
                    self.start_monitor(ivalue)
            else:
                # already existed in another state
                for my_hash, my_dict in ivalue.iteritems():
                    self.update_state(my_hash, 'MONITORING')
                    self.start_vent_collector(self.just_the_hash(ivalue))
                    self.start_monitor(ivalue)

        if 'poseidon.algos.eval_dev_class' in itype:
            # ivalue = classificationtype:<string>
            # result form eval device classifier with
            # dev hash attached to end of routing key
            dev_hash = itype.split('.')[-1]
            prev_class = self.check_db(dev_hash, 'dev_classification')

            monitoring_id = self.monitoring[dev_hash]
            temp_d = {dev_hash: monitoring_id}

            # self.stop_monitor(monitoring_id)
            self.stop_monitor(temp_d)

            self.logger.debug('stopping monitoring on:' + itype)
            self.logger.debug('classified as:{0}'.format(ivalue))
            self.logger.debug('classified previously {0}'.format(prev_class))
            if ivalue == prev_class:
                self.logger.debug(
                    '***** allowing endpoint {0}:{1}'.format(itype, temp_d))
                self.endpoint_allow(temp_d)
            else:
                self.logger.debug(
                    '***** shutting down endpoint:{0}:{1}'.format(itype, temp_d))
                self.endpoint_shutdown(temp_d)

    def do_work(self, item):
        '''schuffle item to the correct handlers'''
        itype, ivalue = self.make_type_val(item)

        self.handle_item(itype, ivalue)
        handle_list = self.Scheduler.get_handlers(itype)
        if handle_list is not None:
            for handle in handle_list:
                handle(ivalue)
        handle_list = self.Investigator.get_handlers(itype)
        if handle_list is not None:
            for handle in handle_list:
                handle(ivalue)

    def process(self):
        ''' processing loop  '''
        testing_loop = 10

        flag = False
        if getenv('PRODUCTION', 'False') == 'True':
            flag = True

        self.logger.debug('PRODUCTION = {0}'.format(
            getenv('PRODDUCTION', 'False')))
        while not self.shutdown_flag and testing_loop > 0:
            item = None
            workfound = False
            start = time.clock()
            time.sleep(1)

            if not flag:
                testing_loop = testing_loop - 1

            # type , value
            self.logger.debug('about to look for work')
            try:
                item = self.m_queue.get(False)
                self.logger.debug('item:{0}'.format(item))
                self.logger.debug('found work')
                workfound = True
            except Queue.Empty:
                pass

            self.logger.debug('done looking for work!')

            if workfound:  # pragma no cover
                self.do_work(item)

            self.print_state()

            elapsed = time.clock()
            elapsed = elapsed - start

            log_line = 'time to run eventloop is {0} ms' .format(
                elapsed * 1000)
            self.logger.debug(log_line)
        self.logger.debug('Shutting Down')

    def print_state(self):
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
            same_old(self.logger, s, l, self.endpoint_states)


def main(skip_rabbit=False):
    ''' main function '''
    pmain = PoseidonMain(skip_rabbit=skip_rabbit)

    if not skip_rabbit:
        rabbit = Rabbit_Base()
        host = 'poseidon-rabbit'
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_main'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = rabbit.make_rabbit_connection(host, exchange, queue_name,
                                               binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        rabbit.start_channel(pmain.rabbit_channel_local, callback,
                             'poseidon_main', pmain.m_queue)
        pmain.Scheduler.schedule_thread.start()
        # def start_channel(self, channel, callback, queue):
    pmain.process()
    return True


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
