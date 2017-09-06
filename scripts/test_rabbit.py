"""
Simple script to establish rabbit connection
for testing receiving messages.

@author: lanhamt
Created on September 13, 2016
"""
import os
import sys
import datetime
import time
import pika


def rabbit_init(host, exchange, queue_name, rabbit_rec):  # pragma: no cover
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
            print 'connected to rabbitmq...'
        except Exception as e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            time.sleep(2)
            wait = True

    if rabbit_rec:
        binding_keys = ['poseidon.algos.eval_dev_class.#']
        if not binding_keys:
            ostr = 'Usage: {0} [binding_key]...'.format(sys.argv[0])
            print(ostr)
            sys.exit(1)

        for binding_key in binding_keys:
            channel.queue_bind(exchange=exchange,
                               queue=queue_name,
                               routing_key=binding_key)

    print(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


def callback(ch, method, properties, body):
    print 'MESSAGE at ' + str(datetime.datetime.now()) + ': ' + body
    print 'key is :', method.routing_key.split('.')[-1]


if __name__ == '__main__':
    host = 'localhost'
    exchange = 'topic-poseidon-internal'
    queue_name = 'test_queue'
    key = 'poseidon.algos.eval_dev_class.#'

    ch, conn = rabbit_init(host, exchange, queue_name, True)
    ch.basic_consume(callback, queue=queue_name, no_ack=True, consumer_tag=key)
    ch.start_consuming()
