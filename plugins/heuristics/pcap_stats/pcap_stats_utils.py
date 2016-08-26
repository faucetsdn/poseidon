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
utils module for pcap_stats;
includes TimeRecord, MachineNode,
and FlowRecord classes

Created on 28 July 2016
@author: lanhamt
"""
import time
from collections import defaultdict
from datetime import datetime

import statistics


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
                self.time_record.update_received(
                    '%s %s' % (pcap['date'], pcap['time']))
        else:
            self.num_packets_sent += 1
            self.packet_lens_sent.append(length)
            self.machines_sent_to[addr] += 1
            if pcap:
                self.time_record.update_sent(
                    '%s %s' % (pcap['date'], pcap['time']))

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
