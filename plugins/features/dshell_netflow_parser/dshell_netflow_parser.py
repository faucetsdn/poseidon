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
DShell netflow parser plugin

Created on 13 June 2016
@author: Charlie Lewis, Abhi Ganesh

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
        keys:   poseidon.dshell
"""

import pika
import subprocess
import sys


def get_path():
    path = None
    try:
        path = sys.argv[1]
    except:
        print "no path provided, quitting."
    return path


def connections():
    """Handle connection setup to rabbitmq service"""
    channel = None
    connection = None
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='poseidon-rabbit'))
        channel = connection.channel()

        channel.exchange_declare(exchange='topic-poseidon-internal',
                                 type='topic')
    except:
        print "unable to connect to rabbitmq, quitting."
    return channel, connection


def run_tool(path):
    """Tool entry point"""
    routing_key = 'poseidon.dshell'
    print "processing pcap results..."
    subprocess.Popen(
        '/Dshell/dshell-decode -o /tmp/results.out -d netflow ' +
        path,
        shell=True,
        stdout=subprocess.PIPE).wait()

    channel, connection = connections()
    print "sending pcap results..."

    try:
        with open('/tmp/results.out', 'r') as f:
            for rec in f:
                data = {}
                rec = rec.strip()
                fields = rec.split()
                try:
                    data["date"] = fields[0].strip()
                    data["time"] = fields[1].strip()
                    data["src_ip"] = fields[2].strip()
                    data["dst_ip"] = fields[4].strip()
                    data["src_country_code"] = fields[5].strip()[1:]
                    data["dst_country_code"] = fields[7].strip()[:-1]
                    data["protocol"] = fields[8].strip()
                    data["src_port"] = fields[9].strip()
                    data["dst_port"] = fields[10].strip()
                    data["src_packets"] = fields[11].strip()
                    data["dst_packets"] = fields[12].strip()
                    data["src_bytes"] = fields[13].strip()
                    data["dst_bytes"] = fields[14].strip()
                    data["duration"] = fields[15].strip()
                    data["tool"] = "dshell_netflow"
                    message = str(data)

                    if channel:
                        channel.basic_publish(
                            exchange='topic_recs', routing_key=routing_key, body=message)
                        print " [x] Sent %r:%r" % (routing_key, message)
                except:
                    pass
    except:
        pass

    try:
        connection.close()
    except:
        pass

if __name__ == '__main__':
    path = get_path()
    if path:
        run_tool(path)
