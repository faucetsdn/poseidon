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
Created on 24 August 2016
@author: bradh41, tlanham

Evaluation module for deep learning
model to classify packets based on
hex headers.

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue:
"""
import cPickle
import logging


module_logger = logging.getLogger(__name__)


def get_path():
    try:
        path_name = sys.argv[1]
    except:
        module_logger.debug('no argv[1] for pathname')
        path_name = None
    return path_name


def get_host():
    """
    Checks for poseidon host env
    variable and returns it if found,
    otherwise logs error.
    """
    if 'POSEIDON_HOST' in os.environ:
        return os.environ['POSEIDON_HOST']
    else:
        module_logger.debug('POSEIDON_HOST environment variable not found')
        return None


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
            channel.exchange_declare(exchange=exchange, type='topic')
            result = channel.queue_declare(queue=queue_name, exclusive=True)
            wait = False
            module_logger.info('connected to rabbitmq...')
            print 'connected to rabbitmq...'
        except Exception, e:
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


def load_model(file_name):
    """
    Given a file name for a pickel-serialized
    evaluation function in byte form, loads the
    function and returns it on success, otherwise
    returns None.
    """
    try:
        f = open(file_name, 'rb')
        eval_model = cPickle.load(f)
        f.close()
        return eval_model
    except:
        module_logger.error(
            'Failed to load model evaluation function from: ' + file_name)
        return None


if __name__ == '__main__':
    host = 'poseidon-rabbit'
    exchange = 'topic-poseidon-internal'
    queue_name = 'NAME'  # fix this
    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue_name)
    load_model('deep_eval.save')
