# -*- coding: utf-8 -*-
"""
Created on 21 August 2017
@author: dgrossman
"""
import threading
import time
from functools import partial

import pika

from poseidon.helpers.log import Logger


class Rabbit(object):
    '''
    Base Class for RabbitMQ
    '''

    def __init__(self):
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger

    def make_rabbit_connection(self, host, port, exchange, queue_name, keys,
                               total_sleep=float('inf')):  # pragma: no cover
        '''
        Connects to rabbitmq using the given hostname,
        exchange, and queue. Retries on failure until success.
        Binds routing keys appropriate for module, and returns
        the channel and connection.
        '''
        wait = True
        do_rabbit = True
        rabbit_channel = None
        rabbit_connection = None

        while wait and total_sleep > 0:
            try:
                # Starting rabbit connection
                rabbit_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host, port=port)
                )
                rabbit_channel = rabbit_connection.channel()
                rabbit_channel.exchange_declare(exchange=exchange,
                                                exchange_type='topic')
                rabbit_channel.queue_declare(queue=queue_name, exclusive=False)
                self.poseidon_logger.debug(
                    'connected to {0} rabbitmq...'.format(host))
                wait = False
            except Exception as e:
                self.poseidon_logger.debug(
                    'waiting for connection to {0} rabbitmq...'.format(host))
                self.poseidon_logger.debug(str(e))
                time.sleep(2)
                total_sleep -= 2
                wait = True

        if wait:
            do_rabbit = False

        if isinstance(keys, list) and not wait:
            for key in keys:
                self.poseidon_logger.debug(
                    'array adding key:{0} to rabbitmq channel'.format(key))
                rabbit_channel.queue_bind(exchange=exchange,
                                          queue=queue_name,
                                          routing_key=key)

        if isinstance(keys, str) and not wait:
            self.poseidon_logger.debug(
                'string adding key:{0} to rabbitmq channel'.format(keys))
            rabbit_channel.queue_bind(exchange=exchange,
                                      queue=queue_name,
                                      routing_key=keys)

        return rabbit_channel, rabbit_connection, do_rabbit

    def start_channel(self, channel, mycallback, queue, m_queue):
        ''' handle threading for messagetype '''
        self.poseidon_logger.debug(
            'about to start channel {0}'.format(channel))
        channel.basic_consume(partial(mycallback, q=m_queue), queue=queue,
                              no_ack=True)
        mq_recv_thread = threading.Thread(target=channel.start_consuming)
        mq_recv_thread.start()
        return mq_recv_thread
