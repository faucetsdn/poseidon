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


class Rabbit:
    '''
    Base Class for RabbitMQ
    '''

    def __init__(self):
        self.logger = logging.getLogger('rabbit')
        self.connection = None
        self.channel = None
        self.mq_recv_thread = None
        self.queue_name = 'poseidon_main'

    def close(self):
        if self.connection:
            self.connection.close()

    def make_rabbit_connection(self, host, port, exchange, keys,
                               total_sleep=float('inf')):  # pragma: no cover
        '''
        Connects to rabbitmq using the given hostname,
        exchange, and queue. Retries on failure until success.
        Binds routing keys appropriate for module, and returns
        the channel and connection.
        '''
        wait = True
        do_rabbit = True

        while wait and total_sleep > 0:
            try:
                # Starting rabbit connection
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host, port=port)
                )
                self.channel = self.connection.channel()
                self.channel.exchange_declare(
                    exchange=exchange, exchange_type='topic')
                self.channel.queue_declare(
                    queue=self.queue_name, exclusive=False, durable=True)
                self.logger.info(f'Connected to {host} rabbitmq...')
                wait = False
            except Exception as e:
                self.logger.debug(
                    f'Waiting for connection to {host} rabbitmq...')
                time.sleep(2)
                total_sleep -= 2
                wait = True

        if wait:
            do_rabbit = False

        if self.channel is not None and isinstance(keys, list) and not wait:
            for key in keys:
                self.logger.debug(
                    f'Array adding key:{key} to rabbitmq channel')
                self.channel.queue_bind(
                    exchange=exchange, queue=self.queue_name, routing_key=key)

        if isinstance(keys, str) and not wait:
            self.logger.debug(
                f'String adding key:{keys} to rabbitmq channel')
            self.channel.queue_bind(
                exchange=exchange, queue=self.queue_name, routing_key=keys)

        return do_rabbit

    def start_channel(self, mycallback, m_queue):
        ''' Handle threading for messagetype '''
        self.logger.debug(f'About to start channel {self.channel}')
        self.channel.basic_consume(
            self.queue_name, partial(mycallback, q=m_queue))
        self.mq_recv_thread = threading.Thread(
            target=self.channel.start_consuming)
        self.mq_recv_thread.start()
