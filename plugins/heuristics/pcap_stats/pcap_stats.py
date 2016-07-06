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
@author: Travis Lanham
"""


import pika
import ast
import time
from collections import defaultdict


wait = True
while wait:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='topic_recs', type='topic')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        wait = False
        print "connected to rabbitmq..."
    except:
        print "waiting for connection to rabbitmq..."
        time.sleep(2)
        wait = True

binding_keys = sys.argv[1:]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_recs',
                       queue=queue_name,
                       routing_key=binding_key)

print ' [*] Waiting for logs. To exit press CTRL+C'


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
        self.num_packets = 0
        self.packet_lengths = []
        self.machines_sent_to = defaultdict(int)
        self.machines_received_from = defaultdict(int)

    def add_pcap_record(self, length, addr, receiving):
        """
        Adds data for a packet to the MachineNode record.
        Increments the number of packets, then if it is
        receving then updates the addresses and frequency of machines
        this Machine has received from; if sending then updates
        the dict with addresses and frequency of machines it
        has sent to.
        """
        self.num_packets += 1
        self.packet_lengths.append(length)
        if receiving:
            self.machines_received_from[addr] += 1
        else:
            self.machines_sent_to[addr] += 1

    def get_avg_packet_len(self):
        """
        Returns the average length of packets this Machine
        has send and recevied. 
        """
        return sum(self.packet_lengths) / self.num_packets

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

    def update(self, src_addr, s_in_net, dest_addr, d_in_net, length):
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
                node.add_pcap_record(length, dest_addr, False)
                self.machines[src_addr] = node
            else:
                self.machines[src_addr].add_pcap_record(length, dest_addr, False)
        if d_in_net:
            if dest_addr not in self.machines:
                node = MachineNode(dest_addr)
                node.add_pcap_record(length, src_addr, True)
                self.machines[dest_addr] = node
            else:
                self.machines[dest_addr].add_pcap_record(length, src_addr, True)

    def get_machine_node(self, addr):
        """
        Retrieves a MachineNode record for a given address,
        returns None if the record is not in this flow.
        """
        if addr not in self.machines:
            return None
        else:
            return self.machines[addr]


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
    if pcap['src_ip'] in network_machines and pcap['dest_ip'] in network_machines:
        # both machines in network
        flow.update(pcap['src_ip'], True, pcap['dest_ip'], True, pcap['length'])
    elif pcap['src_ip'] in network_machines:
        # machine in network talking to outside
        flow.update(pcap['src_ip'], True, pcap['dest_ip'], False, pcap['length'])
    elif pcap['dest_ip'] in network_machines:
        # outside talking to network machine
        flow.update(pcap['src_ip'], False, pcap['dest_ip'], True, pcap['length'])
    else:
        # neither machine in network (list needs to be updated)
        pass


channel.basic_consume(analyzePcap, queue=queue_name, no_ack=True)
channel.start_consuming()
