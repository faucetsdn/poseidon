import ast
import json
import os
import uuid
from datetime import datetime

import falcon
import redis

from .routes import paths
from .routes import version


class Endpoints(object):

    def on_get(self, req, resp):
        endpoints = []
        for path in paths():
            endpoints.append(version()+path)

        resp.body = json.dumps(endpoints)
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Info(object):

    def on_get(self, req, resp):
        resp.body = json.dumps({'version': 'v0.1.0'})
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class NetworkFull(object):

    def connect_redis(self):
        self.r = None
        try:
            if 'POSEIDON_TRAVIS' in os.environ:
                self.r = redis.StrictRedis(host='localhost',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
            else:
                self.r = redis.StrictRedis(host='redis',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
        except Exception as e:  # pragma: no cover
            return (False, 'unable to connect to redis because: ' + str(e))
        return (True, 'connected')

    def get_dataset(self):
        dataset = []
        status = self.connect_redis()
        if status[0] and self.r:
            try:
                mac_addresses = self.r.smembers('mac_addresses')
                for mac in mac_addresses:
                    node = {}
                    node['mac'] = mac
                    node['ip'] = 0
                    node['segment'] = 0
                    node['port'] = 0
                    node['tenant'] = 0
                    node['record_source'] = 'Poseidon'
                    node['role'] = 'UNDEFINED'
                    node['os'] = 'UNDEFINED'
                    node['behavior'] = 0
                    node['hash'] = '0'
                    node['state'] = 'UNDEFINED'
                    node['previous_states'] = 'UNDEFINED'
                    node['active'] = 0
                    try:
                        ip_address = 'None'
                        ip_info = None
                        mac_info = self.r.hgetall(mac)
                        if 'poseidon_hash' in mac_info:
                            node['hash'] = mac_info['poseidon_hash']
                            try:
                                poseidon_info = self.r.hgetall(
                                    mac_info['poseidon_hash'])
                                if 'endpoint_data' in poseidon_info:
                                    endpoint_data = ast.literal_eval(
                                        poseidon_info['endpoint_data'])
                                    ip_address = endpoint_data['ip-address']
                                    node['ip'] = ip_address
                                    node['segment'] = endpoint_data['segment']
                                    node['port'] = endpoint_data['port']
                                    node['tenant'] = endpoint_data['tenant']
                                    node['active'] = endpoint_data['active']
                                    node['state'] = endpoint_data['state']
                                    node['previous_states'] = endpoint_data['prev_states']
                                    ip_info = self.r.hgetall(ip_address)
                            except Exception as e:  # pragma: no cover
                                print(
                                    'Failed to set all poseidon info because: ' + str(e))
                        if 'timestamps' in mac_info:
                            try:
                                timestamps = ast.literal_eval(
                                    mac_info['timestamps'])
                                ml_info = self.r.hgetall(
                                    mac+'_'+str(timestamps[-1]))
                                if 'labels' in ml_info:
                                    labels = ast.literal_eval(
                                        ml_info['labels'])
                                    node['role'] = labels[0]
                            except Exception as e:  # pragma: no cover
                                print(
                                    'Failed to set all timestamp info because: ' + str(e))
                        if ip_info and 'short_os' in ip_info:
                            short_os = ip_info['short_os']
                            node['os'] = short_os
                    except Exception as e:  # pragma: no cover
                        print('Failed to set all info because: ' + str(e))
                    dataset.append(node)
            except Exception as e:  # pragma: no cover
                print('Failed to set all macs because: ' + str(e))
        return dataset

    def on_get(self, req, resp):
        network = {}
        dataset = self.get_dataset()
        network['dataset'] = dataset

        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200


class Network(object):

    def connect_redis(self):
        self.r = None
        try:
            if 'POSEIDON_TRAVIS' in os.environ:
                self.r = redis.StrictRedis(host='localhost',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
            else:
                self.r = redis.StrictRedis(host='redis',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
        except Exception as e:  # pragma: no cover
            return (False, 'unable to connect to redis because: ' + str(e))
        return (True, 'connected')

    def get_dataset(self):
        dataset = []
        status = self.connect_redis()
        if status[0] and self.r:
            try:
                mac_addresses = self.r.smembers('mac_addresses')
                for mac in mac_addresses:
                    node = {}
                    # TODO lock in the uid
                    node['uid'] = str(uuid.uuid4())
                    node['mac'] = mac
                    # set as unknown until it's set below
                    node['IP'] = 'UNDEFINED'
                    node['subnet'] = 'UNDEFINED'
                    node['VLAN'] = 'UNDEFINED'
                    node['behavior'] = 'UNDEFINED'
                    node['active'] = 'UNDEFINED'
                    node['state'] = 'UNDEFINED'
                    node['rDNS_host'] = 'UNDEFINED'
                    node['record'] = {}
                    node['role'] = {}
                    node['role']['role'] = 'UNDEFINED'
                    node['os'] = {}
                    node['os']['os'] = 'UNDEFINED'
                    try:
                        short_os = None
                        endpoint_data = {}
                        labels = []
                        confidences = []
                        mac_info = self.r.hgetall(mac)
                        ip_address = 'None'
                        ip_info = None

                        if 'poseidon_hash' in mac_info:
                            try:
                                poseidon_info = self.r.hgetall(
                                    mac_info['poseidon_hash'])
                                if 'endpoint_data' in poseidon_info:
                                    endpoint_data = ast.literal_eval(
                                        poseidon_info['endpoint_data'])
                                    ip_address = endpoint_data['ip-address']
                                    node['IP'] = ip_address
                                    node['VLAN'] = endpoint_data['tenant']
                                    node['state'] = endpoint_data['state']
                                    active = endpoint_data['active']
                                    if active == 1:
                                        node['active'] = 'Active'
                                    elif active == 0:
                                        node['active'] = 'Inactive'
                                    # cheating for now
                                    if ':' in ip_address:
                                        node['subnet'] = ':'.join(
                                            ip_address.split(':')[0:4])+'::0/64'
                                    elif ip_address == 'None':
                                        node['subnet'] = 'Unknown'
                                    else:
                                        node['subnet'] = '.'.join(
                                            ip_address.split('.')[:-1])+'.0/24'
                                    ip_info = self.r.hgetall(ip_address)
                            except Exception as e:  # pragma: no cover
                                print(
                                    'Failed to set all poseidon info because: ' + str(e))
                        if 'timestamps' in mac_info:
                            try:
                                timestamps = ast.literal_eval(
                                    mac_info['timestamps'])
                                node['record']['source'] = 'poseidon'
                                node['record']['timestamp'] = str(
                                    datetime.fromtimestamp(float(timestamps[-1])))
                                ml_info = self.r.hgetall(
                                    mac+'_'+str(timestamps[-1]))
                                if 'poseidon_hash' in mac_info and mac_info['poseidon_hash'] in ml_info:
                                    try:
                                        results = ast.literal_eval(
                                            ml_info[mac_info['poseidon_hash']])
                                        node['behavior'] = results['decisions']['behavior']
                                    except Exception as e:  # pragma: no cover
                                        print(
                                            'Failed to get behavior info because: ' + str(e))
                                if 'labels' in ml_info:
                                    labels = ast.literal_eval(
                                        ml_info['labels'])
                                    node['role']['role'] = labels[0]
                                if 'confidences' in ml_info:
                                    confidences = ast.literal_eval(
                                        ml_info['confidences'])
                                    node['role']['confidence'] = int(
                                        confidences[0]*100)
                            except Exception as e:  # pragma: no cover
                                print(
                                    'Failed to set all timestamp info because: ' + str(e))
                        if ip_info and 'short_os' in ip_info:
                            short_os = ip_info['short_os']
                            node['os']['os'] = short_os
                    except Exception as e:  # pragma: no cover
                        print('Failed to set all info because: ' + str(e))
                    dataset.append(node)
            except Exception as e:  # pragma: no cover
                print('Failed to set all macs info because: ' + str(e))

        return dataset

    def get_configuration(self):
        configuration = {}
        return configuration

    def on_get(self, req, resp):
        network = {}
        dataset = self.get_dataset()
        configuration = self.get_configuration()

        network['dataset'] = dataset
        network['configuration'] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
