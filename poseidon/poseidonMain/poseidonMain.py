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
"""
poseidonMain

Created on 29 May 2016

@author: dgrossman, lanhamt

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue(in):  algos_classifiers
        keys:   poseidon.algos.#
"""
import json
import logging
import logging.config
import time
from os import getenv

import pika
from Investigator.Investigator import investigator_interface
from Scheduler.Scheduler import scheduler_interface

from Config.Config import config_interface

# class NullHandler(logging.Handler):
#     def emit(self, record):
#         pass

# h = NullHandler()
#  module_logger = logging.getLogger(__name__).addHandler(h)
module_logger = logging.getLogger(__name__)

class PoseidonMain(object):

    def __init__(self):
        self.skipRabbit = False
        self.logger = module_logger
        self.logger.debug('logger started')
        logging.basicConfig(level=logging.DEBUG)
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
            k, v = item
            self.mod_configuration[k] = v

        self.init_logging()

    def init_logging(self):
        config = None

        path = getenv('loggingFile', None)

        if path is None:
            path = self.mod_configuration.get('loggingFile', None)

        if path is not None:
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def handle(self, t, v):
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
        exchange = 'topic_poseidon_internal'
        queue_name = 'algos_classifiers'
        binding_key = 'poseidon.algos.#'
        wait = True
        while wait:
            try:
                params = pika.ConnectionParameters(host=host)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange, type='topic')

                result = channel.queue_declare(
                    queue=queue_name, exclusive=True)

                wait = False
                self.logger.info('connected to rabbitmq...')
            except:
                self.logger.info('waiting for connection to rabbitmq...')
                time.sleep(2)
                wait = True

        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=binding_key)

        self.rabbit_connection = connection
        self.rabbit_channel = channel

    def processQ(self):
        x = 10

        flag = False 
        if getenv('PRODUCTION','False')=='True':
            flag=True

        self.logger.debug('PRODUCTION = %s' %(getenv('PRODDUCTION','False')))
  
        while not self.shutdown and x > 0:
            start = time.clock()
            time.sleep(1)

	    if not flag:
            	x = x - 1

            # type , value
            t, v = self.get_queue_item()

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

            logLine = 'time to run eventloop is %0.3f ms' % (elapsed * 1000)
            self.logger.debug(logLine)


def main(skipRabbit=False):
    pmain = PoseidonMain()
    pmain.skipRabbit = skipRabbit
    if not skipRabbit:
        pmain.init_rabbit()  # pragma: no cover
    pmain.processQ()
    return True

if __name__ == '__main__':  # pragma: no cover
    main(skipRabbit=False)
