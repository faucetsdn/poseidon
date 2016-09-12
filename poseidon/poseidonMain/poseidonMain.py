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
    queue(in):  poseidon_internals
        keys:   poseidon.algos.#,poseidon.action.#
'''
import json
import logging
import logging.config
import Queue
import threading
import time
import types
from functools import partial
from os import getenv

import pika

from poseidon.poseidonMain.Config.Config import config_interface
from poseidon.poseidonMain.Investigator.Investigator import investigator_interface
from poseidon.poseidonMain.Scheduler.Scheduler import scheduler_interface

# class NullHandler(logging.Handler):
#     def emit(self, record):
#         pass

# h = NullHandler()
#  module_logger = logging.getLogger(__name__).addHandler(h)
logging.basicConfig(level=logging.DEBUG)
module_logger = logging.getLogger(__name__)


def callback(ch, method, properties, body, q=None):
    module_logger.debug('got a message: {0}'.format(body))
    print body
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        module_logger.error('posedionMain workQueue is None')


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

        for item in self.Config.get_section(self.config_section_name):
            my_k, my_v = item
            self.mod_configuration[my_k] = my_v

        self.init_logging()

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

    def make_type_val(self, item):
        ''' search messages and act  '''
        endpoint = None
        value = None

        if isinstance(item, types.DictionaryType):
            endpoint = item.get('endpoint')
            value = item.get('value')
            if endpoint == 'Main':
                if value == 'shutdown':
                    self.shutdown = True
            return endpoint, value
        if isinstance(item, types.StringType):
            endpoint = 'None'
            value = item
            return endpoint, value

        endpoint, value = 'Error', 'Error'
        return endpoint, value

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
        queue_name = 'poseidon_internals'
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

    def process(self):
        ''' process  '''
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
                workfound = True
            except Queue.Empty:
                pass

            self.logger.debug('done looking for work!')

            if workfound:  # pragma no cover

                itype, ivalue = self.make_type_val(item)

                handle_list = self.Scheduler.get_handlers(itype)
                if handle_list is not None:
                    for handle in handle_list:
                        handle(ivalue)
                handle_list = self.Investigator.get_handlers(itype)
                if handle_list is not None:
                    for handle in handle_list:
                        handle(ivalue)

            elapsed = time.clock()
            elapsed = elapsed - start

            log_line = 'time to run eventloop is {0} ms' .format(
                elapsed * 1000)
            self.logger.debug(log_line)
        self.logger.debug('Shutting Down')


def main(skip_rabbit=False):
    ''' main function '''
    pmain = PoseidonMain(skip_rabbit=skip_rabbit)
    if not skip_rabbit:
        pmain.init_rabbit()
        pmain.start_channel(pmain.rabbit_channel_local,
                            callback, 'poseidon_internals')
        # def start_channel(self, channel, callback, queue):
    pmain.process()
    return True

if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
