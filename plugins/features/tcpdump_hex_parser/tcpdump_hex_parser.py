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
Tcpdump hex parser plugin

Created on 13 June 2016
@author: Charlie Lewis, David Grossman, Travis Lanham

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
        keys:   poseidon.tcpdump_parser
                poseidon.tcpdump_parser.dns
"""
import subprocess
import sys
import pika


def get_path():
    path = None
    try:
        path = sys.argv[1]
    except:
        print 'no path provided, quitting.'
    return path


def connections():
    """Handle connection setup to rabbitmq service"""
    channel = None
    connection = None
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='poseidon-rabbit'))
        channel = connection.channel()

        channel.exchange_declare(exchange='topic_poseidon_internal',
                                 type='topic')
    except:
        print 'unable to connect to rabbitmq, quitting.'
    return channel, connection


def parse_header(line):
    """Parse output of tcpdump of pcap file, extract:
        time
        date
        ethernet_type
        protocol
        source ip
        source port (if it exists)
        destination ip
        destination port (if it exists)
        length of the data
        resolved addresses (if they exist, for dns traffic only)
        """
    ret_dict = {}
    h = line.split()
    date = h[0]
    time = h[1]
    ret_dict['raw_header'] = line
    ret_dict['date'] = date
    ret_dict['time'] = time
    ret_dict['ethernet_type'] = h[2]

    if h[2] == 'IP6':
        """
        Conditional formatting based on ethernet type.
        IPv4 format: 0.0.0.0.port
        IPv6 format (one of many): 0:0:0:0:0:0.port
        """
        ret_dict['src_port'] = h[3].split('.')[-1]
        ret_dict['src_ip'] = h[3].split('.')[0]

        ret_dict['dest_port'] = h[5].split('.')[-1].split(':')[0]
        ret_dict['dest_ip'] = h[5].split('.')[0]
    else:
        if len(h[3].split('.')) > 4:
            ret_dict['src_port'] = h[3].split('.')[-1]
            ret_dict['src_ip'] = '.'.join(h[3].split('.')[:-1])
        else:
            ret_dict['src_ip'] = h[3]

        if len(h[5].split('.')) > 4:
            ret_dict['dest_port'] = h[5].split('.')[-1].split(':')[0]
            ret_dict['dest_ip'] = '.'.join(h[5].split('.')[:-1])
        else:
            ret_dict['dest_ip'] = h[5].split(':')[0]

    ret_dict['protocol'] = h[6]

    try:
        """
        If the packet is a DNS request or response, parse it
        correctly for length and if response from DNS server then
        parse the addresses resolved, add to list, and enter in return
        directory. 'A' if for resolved IPv4, 'AAAA' for IPv6
        """
        if ret_dict['src_port'] == '53' or ret_dict['dst_port'] == '53':
            ret_dict['length'] = int(h[-1][1:-1])
            if ret_dict['src_port'] == '53':
                resolved_addrs = []
                if ' A ' in line:
                    for addr in line.split(' A ')[1:]:
                        clean_addr = addr.replace(',', '').split()[0]
                        resolved_addrs.append(clean_addr)
                if ' AAAA ' in line:
                    for addr in line.split(' AAAA ')[1:]:
                        clean_addr = addr.replace(',', '').split()[0]
                        resolved_addrs.append(clean_addr)
                if resolved_addrs:
                    ret_dict['dns_resolved'] = resolved_addrs
    except:
        try:
            ret_dict['length'] = int(line.split(' length ')[1].split(':')[0])
        except:
            ret_dict['length'] = 0

    return ret_dict


def parse_data(line, length):
    """Parse hex data from tcpdump of pcap file"""
    ret_str = ''
    h, d = line.split(':', 1)
    ret_str = d.strip().replace(' ', '')
    if length != 0:
        ret_str = ret_str[:-(2 * length)]
    return ret_str


def return_packet(line_source):
    """Create a packet dictionary
    'data' field -> ascii hex values of the packet header and data
    'time' field -> time of packet capture
    'date' field -> date of packet capture
    'ethernet_type' field -> type of ethernet of packet capture
    'protocol' field -> protocol of packet capture
    'src_ip' field -> source ip address of packet capture
    'src_port' field -> source port of packet capture
    'dest_ip' field -> destination ip address of packet capture
    'dest_port' field -> destination port of packet capture
    'length' field -> length of data in packet capture
    'raw_header' field -> raw storage of the tcpdump header"""
    ret_data = ''
    ret_header = {}
    ret_dict = {}
    for line in line_source:
        line_strip = line.strip()
        is_header = not line_strip.startswith('0x')
        if is_header:
            # parse header
            ret_header = parse_header(line_strip)
            if not ret_data:
                # no data read, just update the header
                ret_dict.update(ret_header)
            else:
                # put the data into the structure and yeild
                ret_dict['data'] = ret_data
                ret_data = ''
                yield ret_dict
        else:
            # concatenate the data
            data = parse_data(line_strip, ret_header['length'])
            ret_data = ret_data + data


def run_tool(path):
    """
    Tool entry point
    """
    print 'processing pcap results...'
    channel, connection = connections()
    proc = subprocess.Popen(
        'tcpdump -nn -tttt -xx -r ' + path,
        shell=True,
        stdout=subprocess.PIPE)
    for packet in return_packet(proc.stdout):
        message = str(packet)
        if 'dns_resolved' in packet:
            routing_key = 'poseidon.tcpdump_parser.dns'
        else:
            routing_key = 'poseidon.tcpdump_parser'
        if channel is not None:
            channel.basic_publish(exchange='topic_poseidon_internal',
                                  routing_key=routing_key,
                                  body=message)
        print ' [x] Sent %r:%r' % (routing_key, message)
    try:
        connection.close()
    except:
        pass

if __name__ == '__main__':
    path = get_path()
    if path:
        run_tool(path)
