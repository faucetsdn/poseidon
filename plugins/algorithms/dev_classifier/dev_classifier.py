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
import pika
import sys


"""
wait = True
while wait:
    try:
        params = pika.ConnectionParameters(host='poseidon-rabbit')
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange='topic_poseidon_internal', type='topic')

        in_queue = 'features_flowparser'
        result = channel.queue_declare(queue=in_queue, exclusive=True)

        wait = False
        print 'connected to rabbitmq...'
    except:
        print 'waiting for connection to rabbitmq...'
        time.sleep(2)
        wait = True

binding_keys = sys.argv[1:]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)
for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_poseidon_internal',
                       queue=in_queue,
                       routing_key=binding_key)
print ' [*] Waiting for logs. To exit press CTRL+C'


def callback(ch, method, properties, body):
    """
    """
    global channel
    message = 'ml results'
    routing_key = 'poseidon.algos.dev_class'
    channel.basic_publish(exchange='topic_poseidon_internal',
                          routing_key=routing_key,
                          body=message)


channel.basic_consume(callback, queue=in_queue, no_ack=True)
channel.start_consuming()
"""
