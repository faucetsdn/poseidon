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
'''
Take parsed pcaps and add all resolved addresses from dns
to reference new traffic against to determine
whether a dns lookup has occured recently for dest address.
Maintains a dict of machine_addr->DNSRecord for each machine,
where the DNSRecord is a time store for resolved addresses.

Created on 22 June 2016
@author: Travis Lanham, Charlie Lewis

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue(in):  features_tcpdump
        keys:   poseidon.tcpdump_parser.dns.#
'''
import ast
import copy
import logging
import time
import os
import sys
import pika

module_logger = logging.getLogger(__name__)


def get_path():
    try:
        path_name = sys.argv[1]
    except BaseException:
        module_logger.debug('no argv[1] for pathname')
        path_name = None
    return path_name


def get_host():
    """
    Checks for poseidon host env
    variable and returns it if found,
    otherwise logs error.
    """
    if 'POSEIDON_HOST' in os.environ:
        return os.environ['POSEIDON_HOST']
    else:
        module_logger.debug('POSEIDON_HOST environment variable not found')
        return None


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
            channel.exchange_declare(exchange=exchange, type='topic')
            result = channel.queue_declare(queue=queue_name, exclusive=True)
            wait = False
            module_logger.info('connected to rabbitmq...')
            print 'connected to rabbitmq...'
        except Exception as e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    if rabbit_rec:
        binding_keys = ['poseidon.tcpdump_parser.dns.#']

        for binding_key in binding_keys:
            channel.queue_bind(exchange=exchange,
                               queue=queue_name,
                               routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


class DNSRecord():
    '''
    Class to keep track of resolved dns
    requests for a machine with address addr
    - stores resolved addresses with
    a time-to-live so they will be removed from
    the dict after that time expires.
    '''

    def __init__(self, addr):
        self.name = addr
        self.resolved = {}

    # 7 min default duration - approx time of
    # os dns cache with long ttl
    def add(self, addr, duration=420):
        self.resolved[addr] = time.time() + duration

    def __contains__(self, addr):
        '''
        Checks if address is in the resolved
        dict. If time is expired, deletes
        entry and returns False.
        '''
        if addr not in self.resolved:
            return False
        if time.time() < self.resolved[addr]:
            return True
        else:
            del self.resolved[addr]
            return False

    def __iter__(self):
        '''
        Returns valid addresses from resolved
        dict, if time is expired then deletes
        and does not yield.
        '''
        for a in copy.deepcopy(self.resolved):
            if time.time() < self.resolved[a]:
                yield a
            else:
                del self.resolved[a]


network_machines = []
dns_records = {}


def verify_dns_record(ch, method, properties, body):
    '''
    Takes parsed packet as string, if dns packet then
    adds resolved addresses to record of addresses for that machine,
    otherwise checks that the source address is in-network
    (out of network to in-network traffic isn't applicable to dns validation)
    and flags if it destination address was not resolved by the machine.
    '''
    global network_machines
    global dns_records

    packet = ast.literal_eval(body)
    src_addr = packet['src_ip']
    if src_addr in network_machines:
        if 'dns_resolved' in packet:
            # if dns packet then update resolved addresses
            if src_addr in dns_records:
                for addr in packet['dns_resolved']:
                    dns_records[src_addr].add(addr)
            else:
                new_record = DNSRecord(src_addr)
                for addr in packet['dns_resolved']:
                    new_record.add(addr)
                dns_records[src_addr] = new_record
        else:
            # if outbound traffic to non-resolved ip, flag
            if packet['dest_ip'] not in dns_records[src_addr]:
                return 'TODO: signaling packet of interest'


def run_plugin(path, host):
    exchange = 'topic-poseidon-internal'
    queue_name = 'features_tcpdump'
    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue_name,
                                      rabbit_rec=True)
    channel.basic_consume(verify_dns_record,
                          queue=queue_name,
                          no_ack=True,
                          consumer_tag='poseidon.tcpdump_parser.dns.#')
    channel.start_consuming()


if __name__ == '__main__':
    path_name = get_path()
    host = get_host()
    if path_name and host:
        run_plugin(path_name, host)
