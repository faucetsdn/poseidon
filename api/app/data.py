import ast
import json
import os
from copy import deepcopy

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
        resp.body = json.dumps({'version': 'v0.1.1'})
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Nodes():

    def __init__(self, fields):
        self.nodes = []
        self.node = {}
        for field in fields:
            self.node[field] = fields[field]

    def connect_redis(self):
        self.r = None
        try:
            if 'POSEIDON_TRAVIS' in os.environ:
                self.r = redis.StrictRedis(host='localhost',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
            else:  # pragma: no cover
                self.r = redis.StrictRedis(host='redis',
                                           port=6379,
                                           db=0,
                                           decode_responses=True)
        except Exception as e:  # pragma: no cover
            return (False, 'unable to connect to redis because: ' + str(e))
        return (True, 'connected')

    def build_nodes(self):
        status = self.connect_redis()
        if status[0] and self.r:
            mac_addresses = []
            try:
                mac_addresses = self.r.smembers('mac_addresses')
            except Exception as e:  # pragma: no cover
                print(
                    'Unable to retrieve any endpoints because: {0}'.format(str(e)))

            for mac in mac_addresses:
                node = deepcopy(self.node)
                # special cases
                if 'mac' in node:
                    node['mac'] = mac

                # grab from mac info
                mac_info = {}
                try:
                    mac_info = self.r.hgetall(mac)
                except Exception as e:  # pragma: no cover
                    print(
                        'Unable to retrieve endpoint metadata because: {0}'.format(str(e)))

                # grab from endpoint data
                if 'poseidon_hash' in mac_info:
                    if 'id' in node:
                        node['id'] = mac_info['poseidon_hash']
                    try:
                        poseidon_info = self.r.hgetall(
                            mac_info['poseidon_hash'])

                        if 'endpoint_data' in poseidon_info:
                            endpoint_data = ast.literal_eval(
                                poseidon_info['endpoint_data'])
                            for key in node:
                                if key in endpoint_data:
                                    node[key] = endpoint_data[key]
                            if 'ipv4' in node:
                                try:
                                    ipv4 = endpoint_data['ipv4']
                                    if 'ipv4_subnet' in node:
                                        if '.' in ipv4:
                                            node['ipv4_subnet'] = '.'.join(
                                                ipv4.split('.')[:-1])+'.0/24'
                                        else:
                                            node['ipv4_subnet'] = 'Unknown'
                                    ipv4_info = self.r.hgetall(ipv4)
                                    if ipv4_info and 'short_os' in ipv4_info:
                                        node['ipv4_os'] = ipv4_info['short_os']
                                except Exception as e:  # pragma: no cover
                                    print(
                                        'Failed to set IPv4 info because: {0}'.format(str(e)))
                            if 'ipv6' in node:
                                try:
                                    ipv6 = endpoint_data['ipv6']
                                    if 'ipv6_subnet' in node:
                                        if ':' in ipv6:
                                            node['ipv6_subnet'] = ':'.join(
                                                ipv6.split(':')[0:4])+'::0/64'
                                        else:
                                            node['ipv6_subnet'] = 'Unknown'
                                    ipv6_info = self.r.hgetall(ipv6)
                                    if ipv6_info and 'short_os' in ipv6_info:
                                        node['ipv6_os'] = ipv6_info['short_os']
                                except Exception as e:  # pragma: no cover
                                    print(
                                        'Failed to set IPv6 info because: {0}'.format(str(e)))
                    except Exception as e:  # pragma: no cover
                        print(
                            'Failed to set all poseidon info because: {0}'.format(str(e)))

                # grab ml results
                if 'role' in node:
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
                            if 'confidences' in ml_info:
                                confidences = ast.literal_eval(
                                    ml_info['confidences'])
                                node['role_confidence'] = int(
                                    confidences[0]*100)
                            if 'behavior' in node:
                                results = ast.literal_eval(
                                    ml_info[mac_info['poseidon_hash']])
                                node['behavior'] = 1
                                if results['decisions']['behavior'] == 'normal':
                                    node['behavior'] = 0
                        except Exception as e:  # pragma: no cover
                            print(
                                'Failed to set all ML info because: {0}'.format(str(e)))
                self.nodes.append(node)
        return


class NetworkFull(object):

    def get_dataset():
        fields = {'mac': 0, 'id': 'UNDEFINED', 'ipv4': 0, 'ipv6': 0, 'ipv4_subnet': 'UNDEFINED', 'ipv6_subnet': 'UNDEFINED', 'segment': 0, 'port': 0, 'tenant': 0, 'active': 0,
                  'state': 'UNDEFINED', 'prev_states': 'UNDEFINED', 'role': 'UNDEFINED', 'role_confidence': 0, 'behavior': 0, 'ipv4_os': 'UNDEFINED', 'ipv6_os': 'UNDEFINED', 'source': 'UNDEFINED'}
        n = Nodes(fields)
        n.build_nodes()
        return n.nodes

    def on_get(self, req, resp):
        network = {}
        dataset = NetworkFull.get_dataset()
        network['dataset'] = dataset

        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200


class Network(object):

    def get_dataset():
        fields = {'mac': 0, 'ipv4': 0, 'ipv6': 0, 'ipv4_subnet': 'UNDEFINED', 'ipv6_subnet': 'UNDEFINED', 'tenant': 0, 'active': 0, 'state': 'UNDEFINED',
                  'role': 'UNDEFINED', 'role_confidence': 0, 'behavior': 0, 'ipv4_os': 'UNDEFINED', 'ipv6_os': 'UNDEFINED', 'source': 'UNDEFINED'}
        n = Nodes(fields)
        n.build_nodes()
        return n.nodes

    def get_configuration(self):
        configuration = {}
        return configuration

    def on_get(self, req, resp):
        network = {}
        dataset = Network.get_dataset()
        configuration = self.get_configuration()

        network['dataset'] = dataset
        network['configuration'] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
