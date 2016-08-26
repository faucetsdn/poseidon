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

Machine learning plugin for classifying
ports from tcp packets.

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue(in):  features_flowparser
        keys:   poseidon.flowparser

    keys(out):  poseidon.algos.port_class
"""
import logging

import numpy as np
import pandas as pd
from sklearn import linear_model
from sklearn import preprocessing
from sklearn.cross_validation import train_test_split
from sklearn.metrics import classification_report
import time
import pika
import sys


module_logger = logging.getLogger(__name__)

fd = None


def rabbit_init(host, exchange, queue_name):  # pragma: no cover
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
            #print "connected to rabbitmq..."
        except Exception, e:
            print "waiting for connection to rabbitmq..."
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    binding_keys = sys.argv[1:]
    if not binding_keys:
        ostr = 'Usage: %s [binding_key]...' % (sys.argv[0])
        module_logger.error(ostr)
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


def file_receive(ch, method, properties, body):
    if 'EOF -- FLOWPARSER FINISHED' in body:
        ch.stop_consuming()
        fd.close()
        try:
            port_classifier(ch, 'temp_file')
        except Exception, e:
            module_logger.debug(str(e))
    else:
        fd.write(body + '\n')
        print ' [*] Received %s', body


def port_classifier(channel, file):
    # Read in file
    flow_df = pd.read_csv(file, names=['srcip', 'srcport', 'dstip', 'dstport', 'proto', 'total_fpackets', 'total_fvolume',
                                       'total_bpackets', 'total_bvolume', 'min_fpktl', 'mean_fpktl', 'max_fpktl', 'std_fpktl',
                                       'min_bpktl', 'mean_bpktl', 'max_bpktl', 'std_bpktl', 'min_fiat', 'mean_fiat', 'max_fiat',
                                       'std_fiat', 'min_biat', 'mean_biat', 'max_biat', 'std_biat', 'duration', 'min_active',
                                       'mean_active', 'max_active', 'std_active', 'min_idle', 'mean_idle', 'max_idle', 'std_idle',
                                       'sflow_fpackets', 'sflow_fbytes', 'sflow_bpackets', 'sflow_bbytes', 'fpsh_cnt', 'bpsh_cnt',
                                       'furg_cnt', 'burg_cnt', 'total_fhlen', 'total_bhlen', 'misc'])

    # Remove uneccesary columns
    flow_df = flow_df.drop('misc', axis=1)

    # Filter initial raw dataset to only have ports classified that are
    # specefied
    filtered_df = flow_df.loc[flow_df['dstport'].isin([53, 443, 80]) | flow_df[
        'srcport'].isin([53, 443, 80])]

    # Create stats only array
    stats = filtered_df.ix[:, 'total_fpackets':]

    # Create ports only aray
    ports = filtered_df.apply(lambda x: min(
        x['srcport'], x['dstport']), axis=1)

    # Scale stats info to be fed into classifier
    scaled_stats = preprocessing.scale(stats)

    # Create test and training data
    X_train, X_test, y_train, y_test = train_test_split(
        scaled_stats, ports.values, test_size=0.2, random_state=41)

    # Create logistic regression model
    lgs = linear_model.LogisticRegression(C=1e5)
    overall_accuracy = lgs.fit(X_train, y_train).score(X_test, y_test)
    module_logger.info(str(overall_accuracy))

    # Classification Report for model
    result = lgs.predict(X_test)
    class_report = classification_report(y_test, result)
    module_logger.info(str(class_report))
    print class_report

    message = class_report
    routing_key = 'poseidon.algos.port_class'
    channel.basic_publish(exchange='topic-poseidon-internal',
                          routing_key=routing_key,
                          body=message)

    ostr = ' [x] Sent %r:%r' % (routing_key, message)
    module_logger.info(ostr)


if __name__ == '__main__':
    host = 'poseidon-rabbit'
    exchange = 'topic-poseidon-internal'
    queue_name = 'features_flowparser'
    binding_key = 'poseidon.flowparser'
    fd = open('temp_file', 'w+')

    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue_name)
    channel.basic_consume(file_receive,
                          queue=queue_name,
                          no_ack=True,
                          consumer_tag=binding_key)
    channel.start_consuming()
