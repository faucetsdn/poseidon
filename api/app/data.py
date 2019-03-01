import ast
import json
import os
import time
from copy import deepcopy

import falcon
import redis
from natural.date import duration

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

                        for key in node:
                            if key in poseidon_info:
                                node[key] = poseidon_info[key]

                        if 'ignored' in node and 'ignore' in poseidon_info:
                            node['ignored'] = poseidon_info['ignore']

                        if 'prev_states' in poseidon_info:
                            prev_states = ast.literal_eval(
                                poseidon_info['prev_states'])
                            if 'first_seen' in node:
                                node['first_seen'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
                                    prev_states[0][1])) + ' (' + duration(prev_states[0][1]) + ')'
                            if 'last_seen' in node:
                                node['last_seen'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
                                    prev_states[-1][1])) + ' (' + duration(prev_states[-1][1]) + ')'

                        if 'endpoint_data' in poseidon_info:
                            endpoint_data = ast.literal_eval(
                                poseidon_info['endpoint_data'])
                            for key in node:
                                if key in endpoint_data:
                                    node[key] = endpoint_data[key]
                            if 'ipv4' in node:
                                try:
                                    ipv4 = endpoint_data['ipv4']
                                    if isinstance(ipv4, str) and ipv4 != 'None':
                                        if 'ipv4_subnet' in node:
                                            if '.' in ipv4:
                                                node['ipv4_subnet'] = '.'.join(
                                                    ipv4.split('.')[:-1])+'.0/24'
                                            else:
                                                node['ipv4_subnet'] = 'NO DATA'
                                        ipv4_info = self.r.hgetall(ipv4)
                                        if ipv4_info and 'short_os' in ipv4_info:
                                            node['ipv4_os'] = ipv4_info['short_os']
                                except Exception as e:  # pragma: no cover
                                    print(
                                        'Failed to set IPv4 info because: {0}'.format(str(e)))
                            if 'ipv6' in node:
                                try:
                                    ipv6 = endpoint_data['ipv6']
                                    if isinstance(ipv6, str) and ipv6 != 'None':
                                        if 'ipv6_subnet' in node:
                                            if ':' in ipv6:
                                                node['ipv6_subnet'] = ':'.join(
                                                    ipv6.split(':')[0:4])+'::0/64'
                                            else:
                                                node['ipv6_subnet'] = 'NO DATA'
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
                            if 'behavior' in node and 'poseidon_hash' in mac_info and mac_info['poseidon_hash'] in ml_info:
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

    @staticmethod
    def get_fields():
        return {'id': 'NO DATA', 'mac': 0, 'id': 'NO DATA', 'ipv4': 0,
                'ipv6': 0, 'ipv4_subnet': 'NO DATA',
                'ipv6_subnet': 'NO DATA', 'segment': 0, 'port': 0,
                'tenant': 0, 'active': 0, 'next_state': 'NO DATA',
                'state': 'NO DATA', 'prev_states': 'NO DATA',
                'ignored': 'False', 'first_seen': 'NO DATA',
                'last_seen': 'NO DATA', 'role': 'NO DATA',
                'role_confidence': 0, 'behavior': 0,
                'ipv4_os': 'NO DATA', 'ipv6_os': 'NO DATA',
                'source': 'NO DATA', 'ipv4_rdns': 'NO DATA',
                'ipv6_rdns': 'NO DATA', 'ether_vendor': 'NO DATA'}

    @staticmethod
    def get_dataset():
        fields = NetworkFull.get_fields()
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

    @staticmethod
    def get_fields():
        return {'id': 'NO DATA', 'mac': 0, 'ipv4': 0, 'ipv6': 0,
                'ipv4_subnet': 'NO DATA', 'ipv6_subnet': 'NO DATA',
                'tenant': 0, 'segment': 0, 'port': 0,
                'state': 'NO DATA', 'ignored': 'False',
                'first_seen': 'NO DATA', 'last_seen': 'NO DATA',
                'role': 'NO DATA', 'role_confidence': 0, 'behavior': 0,
                'ipv4_os': 'NO DATA', 'ipv6_os': 'NO DATA',
                'ipv4_rdns': 'NO DATA', 'ipv6_rdns': 'NO DATA',
                'ether_vendor': 'NO DATA'}

    @staticmethod
    def field_mapping():
        return {'id': 'ID', 'mac': 'MAC Address', 'segment': 'Switch',
                'port': 'Port', 'tenant': 'VLAN', 'ipv4': 'IPv4',
                'ipv4_subnet': 'IPv4 Subnet', 'ipv6_subnet': 'IPv6 Subnet',
                'ipv6': 'IPv6', 'ignored': 'Ignored', 'state': 'State',
                'first_seen': 'First Seen', 'last_seen': 'Last Seen',
                'ipv4_os': 'IPv4 OS', 'ipv6_os': 'IPv6 OS', 'role': 'Role',
                'role_confidence': 'Role Confidence', 'behavior': 'Behavior',
                'ipv4_rdns': 'IPv4 rDNS', 'ipv6_rdns': 'IPv6 rDNS',
                'ether_vendor': 'Ethernet Vendor'}

    @staticmethod
    def get_dataset():
        fields = Network.get_fields()
        n = Nodes(fields)
        n.build_nodes()
        return n.nodes

    @staticmethod
    def get_configuration():
        configuration = {'fields': []}
        for field in Network.get_fields():
            configuration['fields'].append(
                {'path': [field], 'displayName': Network.field_mapping()[field], 'groupable': 'true'})
        return configuration

    def on_get(self, req, resp):
        network = {}
        dataset = Network.get_dataset()
        configuration = Network.get_configuration()

        network['dataset'] = dataset
        network['configuration'] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
