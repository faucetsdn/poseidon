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
from Config.Config import config_interface
from Investigator.Investigator import investigator_interface
from Scheduler.Scheduler import scheduler_interface

# class NullHandler(logging.Handler):
#     def emit(self, record):
#         pass

# h = NullHandler()
#  module_logger = logging.getLogger(__name__).addHandler(h)
module_logger = logging.getLogger(__name__)


def callback(ch, method, properties, body, q=None):
    module_logger.debug('got a message: %r', body)
    # TODO more
    print body
    q.put(body)


class PoseidonMain(object):

    def __init__(self):
        ''' poseidonMain initialization '''
        self.skip_rabbit = False

        self.rabbit_connection_local = None
        self.rabbit_channel_local = None

        self.rabbit_connection_vent = None
        self.rabbit_channel_vent = None

        self.logger = module_logger
        self.logger.debug('logger started')
        logging.basicConfig(level=logging.DEBUG)

        self.m_qeueue = Queue.Queue()
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

        path = getenv('loggingFile', None)

        if path is None:
            path = self.mod_configuration.get('loggingFile', None)

        if path is not None:
            with open(path, 'rt') as some_file:
                config = json.load(some_file)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def handle(self, t, v):
        ''' search messages and act  '''
        if t == 'Main':
            if v == 'shutdown':
                self.shutdown = True

    def get_queue_item(self):
        return('t', 'v')

    def init_rabbit(self):  # pragma: no cover
        """
        Continuously loops trying to connect to rabbitmq,
        once connected declares the exchange and queue for
        processing algorithm results.
        """
        host = 'poseidon-rabbit'
        exchange = 'topic-poseidon-internal'
        queue_name = 'algos_classifiers'
        binding_key = 'poseidon.algos.#'
        wait = True
        while wait:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host))
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange, type='topic')
                channel.queue_declare(queue=queue_name, exclusive=True)
                self.logger.debug('connected to %s rabbitMQ', host)
                wait = False
            except Exception as e:
                self.logger.debug('waiting for %s rabbitQM', host)
                self.logger.debug(str(e))
                time.sleep(2)
                wait = True

        if isinstance(keys, types.ListType):
            for key in keys:
                self.logger.debug(
                    'array adding key:%s to rabbitmq channel', key)
                channel.queue_bind(exchange=exchange,
                                   queue=queue_name,
                                   routing_key=key)

        if isinstance(keys, types.StringType):
            self.logger.debug('string adding key:%s to rabbitmq channel', keys)
            channel.queue_bind(exchange=exchange,
                               queue=queue_name, routing_key=keys)

        return channel, connection

    def init_rabbit(self):
        ''' init_rabbit '''
        host = 'poseidon-rabbit'
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_internals'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = self.make_rabbit_connection(
            host, exchange, queue_name, binding_key)
        self.rabbit_channel_local = retval[0]
        self.rabbit_connection_local = retval[1]

    def start_channel(self, channel, callback, queue):
        ''' handle threading for a messagetype '''
        self.logger.debug('about to start channel %s', channel)
        channel.basic_consume(
            partial(callback, q=self.m_qeueue), queue=queue, no_ack=True)
        mq_recv_thread = threading.Thread(target=channel.start_consuming)
        mq_recv_thread.start()

    def process(self):
        ''' process  '''
        testing_loop = 10

        flag = False
        if getenv('PRODUCTION', 'False') == 'True':
            flag = True

        self.logger.debug('PRODUCTION = %s', getenv('PRODDUCTION', 'False'))

        while not self.shutdown and testing_loop > 0:
            item = None
            start = time.clock()
            time.sleep(1)

            if not flag:
                testing_loop = testing_loop - 1

            # type , value
            self.logger.debug('about to look for work')
            try:
                item = self.m_qeueue.get(False)
                self.logger.debug('item:%r', item)
            except Queue.Empty:
                pass

            t = 't'
            v = 'v'
            self.logger.debug('done looking for work!')

            self.handle(t, v)

            handle_list = self.Scheduler.get_handlers(t)
            if handle_list is not None:
                for handle in handle_list:
                    handle(v)
            handle_list = self.Investigator.get_handlers(t)
            if handle_list is not None:
                for handle in handle_list:
                    handle(v)

            elapsed = time.clock()
            elapsed = elapsed - start

            log_line = 'time to run eventloop is %0.3f ms' % (elapsed * 1000)
            self.logger.debug(log_line)


def main(skip_rabbit=False):
    pmain = PoseidonMain()
    pmain.skip_rabbit = skip_rabbit
    if not skip_rabbit:
        pmain.init_rabbit()  # pragma: no cover
        pmain.start_channel(pmain.rabbit_channel_local,
                            callback, 'poseidon_internals')
        # def start_channel(self, channel, callback, queue):
    pmain.process()
    return True

if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
