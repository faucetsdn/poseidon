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
Take parsed pcaps and add all resolved addresses from dns
to reference new traffic against to determine
whether a dns lookup has occured recently for dest address.

Created on 22 June 2016
@author: Travis Lanham, Charlie Lewis
"""


import pika
import copy
import time
import ast

"""
wait = True
while wait:
    try:
        connection = pika.BlockingConnection(pila.ConnectionParameters(host='rabbitmq'))
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
"""


class DNSRecord:
    """
    Class to keep track of resolved dns
    requests - stores resolved addresses with
    a time-to-live so they will be removed from
    the dict after that time expires.
    """
    def __init__(self):
        self.addrs = {}

    # 7 min default duration - approx time of
    # os dns cache with long ttl
    def add(self, addr, duration=420):
        self.addrs[addr] = time.time() + duration

    def __contains__(self, addr):
        if addr not in self.addrs:
            return False
        if time.time() < self.addrs[addr]:
            return True
        else:
            del self.addrs[addr]
            return False

    def __iter__(self):
        for a in copy.deepcopy(self.addrs):
            if time.time() < self.addrs[a]:
                yield a
            else:
                del self.addrs[a]


resolved_addresses = DNSRecord()
network_machines = []


def verify_dns_record(ch, method, properties, body):
    """
    Takes parsed packet as string, if dns packet then
    adds resolved addresses to record of addresses,
    otherwise checks that outbound request ip is in
    record.

    NOTE: outgoing check only looks if destination port
    if 80 (for regular HTTP traffic), should be improved.
    """
    packet = ast.literal_eval(body)
    global resolved_addresses
    if 'dns_resolved' in packet:
        # if dns packet then update resolved addresses
        for addr in packet['dns_resolved']:
            resolved_addresses.add(addr)
    else:
        # if outbound traffic to non-resolved ip, flag
        if packet['dest_ip'] not in network_machines:
            if packet['dest_ip'] not in resolved_addresses:
                return "TODO: signaling packet of interest"

"""
channel.basic_consume(verify_dns_record, queue=queue_name, no_ack=True)
channel.start_consuming()
"""
