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
from functools import partial
from os import getenv

import requests

import pika
from poseidon.poseidonMain.Config.Config import config_interface
from poseidon.poseidonMain.Investigator.Investigator import \
    investigator_interface
from poseidon.poseidonMain.Scheduler.Scheduler import scheduler_interface

logging.basicConfig(level=logging.DEBUG)
module_logger = logging.getLogger(__name__)


def callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    module_logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        module_logger.error('posedionMain workQueue is None')


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
        self.shutdown = False

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
        self.monitoring = dict()
        self.shutdown = dict()

        for item in self.Config.get_section(self.config_section_name):
            my_k, my_v = item
            self.mod_configuration[my_k] = my_v

        self.init_logging()

        scan_frequency = int(self.mod_configuration['scan_frequency'])
        url = self.mod_configuration['scan_url']

        self.Scheduler.schedule.every(scan_frequency).seconds.do(
            partial(schedule_job_kickurl, url=url, logger=self.Scheduler.logger))

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

    def start_monitor(self, ivalue):
        ''' start monitoring an address'''
        self.logger.debug('start_monitor:{0},{1}'.format(ivalue, type(ivalue)))
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.start_monitor'
        r_msg = json.dumps(ivalue)

        for my_hash, my_value in ivalue.iteritems():

            if my_hash not in self.monitoring:
                self.logger.debug(
                    'starting monitoring:{0}:{1}'.format(my_hash, my_value))
                # TODO MSG the collector to begin waiting. contents of my_value
                #
                self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                        routing_key=r_key,
                                                        body=r_msg)
                self.monitoring[my_hash] = my_value
            else:
                self.logger.debug(
                    'already being monitored:{0}:{1}'.format(
                        my_hash, my_value))

    def stop_monitor(self, ivalue):
        ''' stop monitoring an address'''

        for my_hash, my_dict in ivalue.iteritems():
            if my_hash in self.monitoring:
                self.monitoring.pop(my_hash)

        self.logger.debug('stop_monitor:{0},{1}'.format(ivalue, type(ivalue)))
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.stop_monitor'
        r_msg = json.dumps(ivalue)
        self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                routing_key=r_key,
                                                body=r_msg)

    def endpoint_shutdown(self, ivalue):
        self.logger.debug('endpoint_shutdown:{0}'.format(ivalue))
        ''' shutdown an endpoint '''
        r_exchange = 'topic-poseidon-internal'
        r_key = 'poseidon.action.endpoint_shutdown'
        r_msg = json.dumps(ivalue)
        self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                routing_key=r_key,
                                                body=r_msg)

    def endpoint_allow(self, ivalue):
        ''' shutdown an endpoint '''
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
            self.shutdown = True
        if itype == 'poseidon.action.new_machine':
            self.logger.debug('***** new machine {0}'.format(ivalue))
            # tell monitor to monitor
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

    def make_rabbit_connection(self, host, exchange, queue_name, keys):  # pragma: no cover
        '''
        Continuously loops trying to connect to rabbitmq,
        once connected declares the exchange and queue for
        processing algorithm results.
        '''
        wait = True
        channel = None
        connection = None

        while wait:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host))
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange, type='topic')
                channel.queue_declare(queue=queue_name, exclusive=True)
                self.logger.debug('connected to {0} rabbitMQ'.format(host))
                wait = False
            except Exception as e:
                self.logger.debug('waiting for {0} rabbitQM'.format(host))
                self.logger.debug(str(e))
                time.sleep(2)
                wait = True

        if isinstance(keys, types.ListType):
            for key in keys:
                self.logger.debug(
                    'array adding key:{0} to rabbitmq channel'.format(key))
                channel.queue_bind(exchange=exchange,
                                   queue=queue_name,
                                   routing_key=key)

        if isinstance(keys, types.StringType):
            self.logger.debug(
                'string adding key:{0} to rabbitmq channel'.format(keys))
            channel.queue_bind(exchange=exchange,
                               queue=queue_name, routing_key=keys)

        return channel, connection

    def init_rabbit(self):  # pragma: no cover
        ''' init_rabbit '''
        host = 'poseidon-rabbit'
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_main'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = self.make_rabbit_connection(
            host, exchange, queue_name, binding_key)
        self.rabbit_channel_local = retval[0]
        self.rabbit_connection_local = retval[1]

        host = 'poseidon-vent'
        exchange = 'topic-vent-poseidon'
        queue_name = 'vent_poseidon'
        binding_key = ['vent.#']

        '''
        retval = self.make_rabbit_connection(
            host, exchange, queue_name, binding_key)
        self.rabbit_channel_vent = retval[0]
        self.rabbit_connection_vent = retval[1]
        '''

    def start_channel(self, channel, mycallback, queue):
        ''' handle threading for a messagetype '''
        self.logger.debug('about to start channel {0}'.format(channel))
        channel.basic_consume(
            partial(mycallback, q=self.m_queue), queue=queue, no_ack=True)
        mq_recv_thread = threading.Thread(target=channel.start_consuming)
        mq_recv_thread.start()

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
        while not self.shutdown and testing_loop > 0:
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
        self.logger.debug('**********MONITORING**********')
        for my_hash, my_value in self.monitoring.iteritems():
            self.logger.debug('M:{0}:{1}'.format(my_hash, my_value))
        self.logger.debug('***********SHUTDOWN***********')
        for my_hash, my_value in self.shutdown.iteritems():
            self.logger.debug('S:{0}:{1}'.format(my_hash, my_value))
        self.logger.debug('******************************')


def main(skip_rabbit=False):
    ''' main function '''
    pmain = PoseidonMain(skip_rabbit=skip_rabbit)
    if not skip_rabbit:
        pmain.init_rabbit()
        pmain.start_channel(pmain.rabbit_channel_local,
                            callback, 'poseidon_main')
        pmain.Scheduler.schedule_thread.start()
        # def start_channel(self, channel, callback, queue):
    pmain.process()
    return True


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
