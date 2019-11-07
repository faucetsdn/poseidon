# -*- coding: utf-8 -*-
"""
Created on 21 August 2017
@author: dgrossman
"""
import logging
import threading
import time
from functools import partial

import pika


class Rabbit(object):
    '''
    Base Class for RabbitMQ
    '''

    def __init__(self):
        self.logger = logging.getLogger('rabbit')

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
                self.logger.debug(
                    'connected to {0} rabbitmq...'.format(host))
                wait = False
            except Exception as e:
                self.logger.debug(
                    'waiting for connection to {0} rabbitmq...'.format(host))
                self.logger.debug(str(e))
                time.sleep(2)
                total_sleep -= 2
                wait = True

        if wait:
            do_rabbit = False

        if rabbit_channel is not None and isinstance(keys, list) and not wait:
            for key in keys:
                self.logger.debug(
                    'array adding key:{0} to rabbitmq channel'.format(key))
                rabbit_channel.queue_bind(exchange=exchange,
                                          queue=queue_name,
                                          routing_key=key)

        if isinstance(keys, str) and not wait:
            self.logger.debug(
                'string adding key:{0} to rabbitmq channel'.format(keys))
            rabbit_channel.queue_bind(exchange=exchange,
                                      queue=queue_name,
                                      routing_key=keys)

        return rabbit_channel, rabbit_connection, do_rabbit

    def start_channel(self, channel, mycallback, queue, m_queue):
        ''' handle threading for messagetype '''
        self.logger.debug(
            'about to start channel {0}'.format(channel))
        channel.basic_consume(queue, partial(mycallback, q=m_queue))
        mq_recv_thread = threading.Thread(target=channel.start_consuming)
        mq_recv_thread.start()
        return mq_recv_thread
