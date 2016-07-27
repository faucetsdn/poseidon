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
import ast
import time
from collections import defaultdict
import statistics
from datetime import datetime
import pika
import thread
from pymongo import MongoClient
import threading


flowRecordLock = threading.Lock()


wait = True
while wait:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='topic_recs', type='topic')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
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
        client = MongoClient(db_ip)
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
    channel.queue_bind(exchange='topic_recs',
                       queue=queue_name,
                       routing_key=binding_key)

print ' [*] Waiting for logs. To exit press CTRL+C'


channel.basic_consume(analyzePcap, queue=queue_name, no_ack=True)
channel.start_consuming()


class TimeRecord:
    """
    Time record class to manage. Takes in time records of
    time concatenated to date for parse format:
    datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    """
    def __init__(self):
        self.first_sent = None
        self.first_received = None
        self.last_sent = None
        self.last_received = None

    def update_sent(self, time):
        """
        Updates sent fields, if first update then
        records the first sent time. Updates the
        latest sent time (both stored as strings).
        """
        if not self.first_sent:
            self.first_sent = time
        self.last_sent = time

    def update_received(self, time):
        """
        Updates received fields, if first update
        then records the first reception time. Always
        updates latest received time (both stored as
        strings).
        """
        if not self.first_received:
            self.first_received = time
        self.last_received = time

    def get_elapsed_time_sent(self):
        """
        Returns elapsed time from first sent to last
        sent, returns delta in microseconds as a float.
        """
        first = datetime.strptime(self.first_sent, '%Y-%m-%d %H:%M:%S.%f')
        latest = datetime.strptime(self.last_sent, '%Y-%m-%d %H:%M:%S.%f')
        return (latest - first).total_seconds() * 1000

    def get_elapsed_time_received(self):
        """
        Returns elapsed time from first sent to last
        received, returns delta in microseconds as a float.
        """
        first = datetime.strptime(self.first_received, '%Y-%m-%d %H:%M:%S.%f')
        latest = datetime.strptime(self.last_received, '%Y-%m-%d %H:%M:%S.%f')
        return (latest - first).total_seconds() * 1000


class MachineNode:
    """
    Record for machine on network,
    keeps track of machines network machine
    has talked to and received from, as well
    as packet statistics (length, frequency of
    communication).
    """
    def __init__(self, addr):
        self.machine_addr = addr
        self.num_packets_sent = 0
        self.num_packets_rec = 0
        self.packet_lens_sent = []
        self.packet_lens_rec = []
        self.machines_sent_to = defaultdict(int)
        self.machines_received_from = defaultdict(int)
        self.time_record = TimeRecord()

    def add_pcap_record(self, length, addr, receiving, pcap=None):
        """
        Adds data for a packet to the MachineNode record.
        Increments the number of packets, then if it is
        receving then updates the addresses and frequency of machines
        this Machine has received from; if sending then updates
        the dict with addresses and frequency of machines it
        has sent to. Updates time record.
        """
        if receiving:
            self.num_packets_rec += 1
            self.packet_lens_rec.append(length)
            self.machines_received_from[addr] += 1
            if pcap:
                self.time_record.update_received('%s %s' % (pcap['date'], pcap['time']))
        else:
            self.num_packets_sent += 1
            self.packet_lens_sent.append(length)
            self.machines_sent_to[addr] += 1
            if pcap:
                self.time_record.update_sent('%s %s' % (pcap['date'], pcap['time']))

    def get_flow_duration(self, direction='sent'):
        """
        Returns flow duration in string format. Takes a
        direction parameter ('sent' or 'received') to
        determine which time delta is returned. 'sent' is
        default.
        """
        if direction == 'sent':
            return self.time_record.get_elapsed_time_sent()
        else:
            return self.time_record.get_elapsed_time_received()

    def get_mean_packet_len(self, direction='sent'):
        """
        Returns the average length of packets this Machine
        has sent and received as a float. Takes a
        direction parameter ('sent' or 'received') to
        determine which mean is returned. 'sent' is
        default.
        """
        if direction == 'sent':
            return statistics.mean(self.packet_lens_sent)
        else:
            return statistics.mean(self.packet_lens_rec)

    def get_packet_len_std_dev(self, direction='sent'):
        """
        Calculates the standard deviation of packet length for
        all conversations to and from this machine.
        """
        try:
            if direction == 'sent':
                return statistics.stdev(self.packet_lens_sent)
            else:
                return statistics.stdev(self.packet_lens_rec)
        except:
            return 'Error retrieving standard deviation.'

    def get_machines_sent_to(self):
        """
        Iterates over dict of machines this Machine has sent
        to and yields the address and frequency of conversation.
        """
        for machine, freq in self.machines_sent_to.iteritems():
            yield machine, freq

    def get_machines_received_from(self):
        """
        Iterates over dict of machines this Machine has received
        from and yields the address and frequency of conversation.
        """
        for machine, freq in self.machines_received_from.iteritems():
            yield machine, freq


class FlowRecord:
    """
    Record to track network flow between
    machines on network. For each machine
    on network maintains a MachineNode that
    keeps track of the machines it has sent to
    and received from and the frequency as well as
    packet length.
    """
    def __init__(self):
        """
        Creates dict of addr->MachineNode to store machine records
        """
        self.machines = {}

    def update(self, src_addr, s_in_net, dest_addr, d_in_net, length, pcap):
        """
        Updates the flow for machines if they are in the
        network. For a packet with a networked source machine,
        gets the record for the source machine and updates the dict
        of machines it has sent to (dest_addr) in its MachineNode.
        For a networked destination machine, gets MachineNode record
        for the machine and updates it with the src_addr that it has
        received from.
        """
        if s_in_net:
            if src_addr not in self.machines:
                node = MachineNode(src_addr)
                node.add_pcap_record(length, dest_addr, False, pcap)
                self.machines[src_addr] = node
            else:
                self.machines[src_addr].add_pcap_record(
                    length, dest_addr, False, pcap)
        if d_in_net:
            if dest_addr not in self.machines:
                node = MachineNode(dest_addr)
                node.add_pcap_record(length, src_addr, True, pcap)
                self.machines[dest_addr] = node
            else:
                self.machines[dest_addr].add_pcap_record(
                    length, src_addr, True, pcap)

    def get_machine_node(self, addr):
        """
        Retrieves a MachineNode record for a given address,
        returns None if the record is not in this flow.
        """
        if addr not in self.machines:
            return None
        else:
            return self.machines[addr]


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
