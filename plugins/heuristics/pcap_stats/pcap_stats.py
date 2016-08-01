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
Given parsed hex pcaps, pull
from rabbitmq and generate statistics
for them, periodically update database with new stats.

NOTE: need to add a periodic database update

Created on 22 June 2016
@author: lanhamt
"""
from pymongo import MongoClient
from pcap_stats_utils import FlowRecord
from pcap_stats_utils import MachineNode
from pcap_stats_utils import TimeRecord
import sys
import ast
import time
import pika
import thread
import threading


flowRecordLock = threading.Lock()


"""
wait = True
while wait:
    try:
        params = pika.ConnectionParameters(host=DOCKER_IP)
        print params
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange='topic_poseidon_internal', type='topic')
        queue_name = 'process_heuristic_stats'
        result = channel.queue_declare(queue=queue_name, exclusive=True)
        wait = False
        print 'connected to rabbitmq...'
    except:
        print 'waiting for connection to rabbitmq...'
        time.sleep(2)
        wait = True


client = None
wait = True
while wait:
    try:
        client = MongoClient()
        client.address
        wait = False
        print 'connected to database...'
    except:
        print 'could not connect to database, retrying...'
        time.sleep(2)


binding_keys = sys.argv[1:]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_poseidon_internal',
                       queue=queue_name,
                       routing_key=binding_key)

print ' [*] Waiting for logs. To exit press CTRL+C'


channel.basic_consume(analyzePcap, queue=queue_name, no_ack=True)
channel.start_consuming()
"""


def db_update_worker():
    """
    Function to be executed by separate worker
    thread to connect to database and update
    based on machines in the flow records. Then
    sleeps for 5 sec before waking up for next
    update

    NOTE: install with
    thread.start_new_thread(db_update_worker)

    ISSUE: add bool to flow record for whether it
    needs to be updated (ie any changes from last
    update) and at end of update, reset it.
    """
    """
    global client
    global flowRecordLock
    while True:
        try:
            client.address  # verify connection
            # check update conditions
            # flowRecordLock.acquire()
            # update
            # flowRecordLock.release()
        except:
            print('database update failed...')
        time.sleep(5)
    """


network_machines = []


def analyze_pcap(ch, method, properties, body, flow):
    """
    Takes pcap record and updates flow graph for
    networked machines.

    TODO: fix flow object - can't have it in the callback,
    determine module useage for fix; right now taken as
    parameter to allow unit testing
    """
    global network_machines

    pcap = ast.literal_eval(body)
    if pcap['src_ip'] in network_machines and \
            pcap['dest_ip'] in network_machines:
        # both machines in network
        flow.update(
            pcap['src_ip'],
            True,
            pcap['dest_ip'],
            True,
            pcap['length'],
            pcap)
    elif pcap['src_ip'] in network_machines:
        # machine in network talking to outside
        flow.update(
            pcap['src_ip'],
            True,
            pcap['dest_ip'],
            False,
            pcap['length'],
            pcap)
    elif pcap['dest_ip'] in network_machines:
        # outside talking to network machine
        flow.update(
            pcap['src_ip'],
            False,
            pcap['dest_ip'],
            True,
            pcap['length'],
            pcap)
    else:
        # neither machine in network (list needs to be updated)
        pass


"""
channel.basic_consume(analyze_pcap, queue=queue_name, no_ack=True)
channel.start_consuming()
"""
