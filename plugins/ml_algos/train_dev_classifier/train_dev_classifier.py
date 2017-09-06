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
Created on 17 August 2016
@author: aganeshLab41, tlanham

Machine learning module for classifying
device type from tcp packets.

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue(in):  features_flowparser
        keys:   poseidon.flowparser

    keys(out):  poseidon.algos.dev_class
"""
import logging
import sys

import pika

module_logger = logging.getLogger(__name__)


def rabbit_init(host, exchange, queue_name):  # pragma: no cover
    """
    Connects to rabbitmq using the given hostname,
    exchange, and queue. Retries on failure until success.
    Binds routing keys appropriate for module, and returns
    the channel and connection.
    """
    wait = True
    while wait:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type='topic')
            result = channel.queue_declare(queue=queue_name, exclusive=True)
            wait = False
            module_logger.info('connected to rabbitmq...')
            print 'connected to rabbitmq...'
        except Exception as e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    binding_keys = sys.argv[1:]
    if not binding_keys:
        ostr = 'Usage: {0} [binding_key]...'.format(sys.argv[0])
        module_logger.error(ostr)
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


def callback(ch, method, properties, body):

    global channel
    message = 'ml results'
    routing_key = 'poseidon.algos.dev_class'
    channel.basic_publish(exchange='topic-poseidon-internal',
                          routing_key=routing_key,
                          body=message)


if __name__ == '__main__':
    host = 'poseidon-rabbit'
    exchange = 'topic-poseidon-internal'
    queue_name = 'features_flowparser'
    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue_name)
    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True,
                          consumer_tag='poseidon.flowparser')
    channel.start_consuming()
