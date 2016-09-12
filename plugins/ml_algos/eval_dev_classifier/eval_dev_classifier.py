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
Created on 12 September 2016
@author: tlanham, aganeshLab41

Evaluation module for logistic regression
device classifier.

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    key (out):	poseidon.algos.eval_dev_class
"""
import cPickle
import logging
import os
import sys
import time
import json
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn import preprocessing
import base64

LABEL_DICT = {0:'Nest', 1: 'TiVo', 2: 'FileServer', 3: 'Printer', 4:'Domain Controller', 5:'SonyTV'}
STORAGE_PORT = '28000'
DATABASE = 'poseidon_records'
COLLECTION = 'models_beta'

module_logger = logging.getLogger(__name__)


def get_path():
    try:
        path_name = sys.argv[1]
    except:
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
        except Exception, e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    if rabbit_rec:
        binding_keys = sys.argv[1:]
        if not binding_keys:
            ostr = 'Usage: {0} [binding_key]...'.format(sys.argv[0])
            module_logger.error(ostr)
            sys.exit(1)

        for binding_key in binding_keys:
            channel.queue_bind(exchange=exchange,
                               queue=queue_name,
                               routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


def load_model():
    try:

        query = {}
        ext = '/v1/storage/query/{database}/{collection}/{query_str}'.format(database=DATABASE,
                                                                             collection=COLLECTION,
                                                                             query_str=query)
        uri = 'http://' + os.environ['POSEIDON_HOST'] + ':' + STORAGE_PORT + ext
        resp = requests.get(uri)
        if resp.status_code != requests.codes.ok:
            print 'error retrieving model from database'
        model = json.loads(resp.body)['docs'][0]['model']
        model_str = base64.b64encode(model)
        model = cPickle.loads(base64.b64decode(model_str))
        return model 
    except:
        print "Failed to load model"
        return None


def eval_dev_classifier(channel, path):
    
    #Load pretrained model 
    model = load_model()

    if not model:
        print "Exiting"
        return 

    #Take flowparser csv and create "test" data
    test_df = pd.read_csv(path,names=['srcip','srcport','dstip','dstport','proto','total_fpackets','total_fvolume',
                                              'total_bpackets','total_bvolume','min_fpktl','mean_fpktl','max_fpktl','std_fpktl',
                                              'min_bpktl','mean_bpktl','max_bpktl','std_bpktl','min_fiat','mean_fiat','max_fiat',
                                              'std_fiat','min_biat','mean_biat','max_biat','std_biat','duration','min_active',
                                              'mean_active','max_active','std_active','min_idle','mean_idle','max_idle','std_idle',
                                              'sflow_fpackets','sflow_fbytes','sflow_bpackets','sflow_bbytes','fpsh_cnt','bpsh_cnt',
                                              'furg_cnt','burg_cnt','total_fhlen','total_bhlen','misc'])

    #extract relevant columns from flowparser csv 
    test_df['port'] = test_df.apply(lambda x: min(x['srcport'],x['dstport']),axis=1)
    test_df = test_df.drop('misc', axis=1)
    test_df = test_df.ix[:,'proto':'port']

    #scale relevant statistics 
    scaled_stats = preprocessing.scale(test_df)

    #make predicition based on incoming data 
    model_prediction = model.predict(scaled_stats)

    count_dict = defaultdict(int)

    for item in model_prediction:
        count_dict[item] += 1

  
    classification = max(count_dict.items(),lambda x: x[1])[0]
    classification = LABEL_DICT[classification]
    print classification

    routing_key = 'poseidon.algos.eval_dev_class'
    channel.basic_publish(exchange='topic-poseidon-internal',
                      routing_key=routing_key,
                      body=classification)




def run_plugin(path, host):  # pragma: no cover
    exchange = 'topic-poseidon-internal'
    queue = 'poseidon_internals'

    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue,
                                      rabbit_rec=False)
    eval_dev_classifier(channel, path)


if __name__ == '__main__':
    path_name = get_path()
    host = get_host()
    if path_name and host:
        run_plugin(path_name, host)
