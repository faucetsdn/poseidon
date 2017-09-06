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
''' Created on  18 July 2016
@author: dgrossman
'''
import logging
import time
import types

import pika

module_logger = logging.getLogger(__name__)


class Algorithm_Base(object):
    '''Bottom most Algorithm class

    Attributes:

    '''

    def __init__(self):
        self.logger = module_logger
        self.rabbit_channel = None
        self.rabbit_connection = None

    def make_rabbit_connection(self, host, exchange, queue_name, keys):  # pragma: no cover
        '''
        Connects to rabbitmq using the given hostname,
        exchange, and queue. Retries on failure until success.
        Binds routing keys appropriate for module, and returns
        the channel and connection.
        '''
        wait = True
        while wait:
            try:
                rabbit_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host))
                rabbit_channel = rabbit_connection.channel()
                rabbit_channel.exchange_declare(
                    queue=queue_name, exclusive=True)
                wait = False
                self.logger.debug('connected to {0} rabbitmq...'.format(host))
            except Exception as e:
                self.logger.debug(str(e))
                self.logger.debug(
                    'waiting for connection to {0} rabbitmq...'.format(host))
                time.sleep(2)
                wait = True

        if isinstance(keys, type.ListType):
            for key in keys:
                self.logger.debug(
                    'array adding key:{0} to rabbitmq channel'.format(key))
                rabbit_channel.queue_bind(exchange=exchange,
                                          queue=queue_name,
                                          routing_key=key)

        if isinstance(keys, type.StringType):
            self.logger.debug(
                'string adding key:{0} to rabbitmq channel'.format(keys))
            rabbit_channel.queue_bind(exchange=exchange,
                                      queue=queue_name,
                                      routing_key=keys)

        return rabbit_channel, rabbit_connection

    def init_rabbit(self, host, exchange, queue_name, bindingkey):  # pragma: no cover
        ''' wire up the rabbit '''
        retval = self.make_rabbit_connection(host,
                                             exchange,
                                             queue_name,
                                             bindingkey)
        self.rabbit_channel = retval[0]
        self.rabbit_connection = retval[1]
