import configparser
import datetime
import json
import os
from copy import deepcopy

import falcon
import requests
from poseidon_core.constants import NO_DATA

from .__init__ import __version__
from .routes import paths
from .routes import version


class Endpoints:

    @staticmethod
    def on_get(_req, resp):
        endpoints = []
        for path in paths():
            endpoints.append(version()+path)

        resp.body = json.dumps(endpoints)
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Info:

    @staticmethod
    def on_get(_req, resp):
        resp.body = json.dumps({'version': __version__})
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Nodes:

    def __init__(self, fields, ip=None):
        self.nodes = []
        self.node = {}
        self.ip = ip
        self.r = None
        self.prometheus_addr = os.environ.get('PROM_ADDR', 'prometheus:9090')
        for field in fields:
            self.node[field] = fields[field]

    def get_prom_addr(self):
        prometheus_ip = None
        prometheus_port = None
        try:
            config = configparser.RawConfigParser()
            config.optionxform = str
            config_path = '/opt/poseidon/poseidon.config'
            config.read_file(open(config_path, 'r'))
            if 'Poseidon' in config:
                if 'prometheus_ip' in config['Poseidon']:
                    prometheus_ip = config['Poseidon']['prometheus_ip']
                if 'prometheus_port' in config['Poseidon']:
                    prometheus_port = config['Poseidon']['prometheus_port']
        except Exception as e:
            print(f'Failed to get config options because {e}, using defaults')
        if prometheus_ip and prometheus_port:
            self.prometheus_addr = prometheus_ip + ':' + prometheus_port

    def scrape_prometheus(self):
        self.get_prom_addr()
        r1 = None
        r2 = None
        r3 = None
        mr = None
        current_time = datetime.datetime.utcnow()
        # 6 hours in the past and 2 hours in the future
        start_time = current_time - datetime.timedelta(hours=6)
        end_time = current_time + datetime.timedelta(hours=2)
        start_time_str = start_time.isoformat()[:-4]+'Z'
        end_time_str = end_time.isoformat()[:-4]+'Z'
        try:
            payload = {'query': 'poseidon_endpoint_metadata',
                       'start': start_time_str, 'end': end_time_str, 'step': '30s'}
            mr = requests.get('http://'+self.prometheus_addr +
                              '/api/v1/query_range', params=payload)
            payload = {'query': 'poseidon_role_confidence_top',
                       'start': start_time_str, 'end': end_time_str, 'step': '30s'}
            r1 = requests.get('http://'+self.prometheus_addr +
                              '/api/v1/query_range', params=payload)
            payload = {'query': 'poseidon_role_confidence_second',
                       'start': start_time_str, 'end': end_time_str, 'step': '30s'}
            r2 = requests.get('http://'+self.prometheus_addr +
                              '/api/v1/query_range', params=payload)
            payload = {'query': 'poseidon_role_confidence_third',
                       'start': start_time_str, 'end': end_time_str, 'step': '30s'}
            r3 = requests.get('http://'+self.prometheus_addr +
                              '/api/v1/query_range', params=payload)
        except Exception as e:
            print(f'Unable to get endpoints from Prometheus because: {e}')
        role_hashes = {}
        hashes = {}
        if r1:
            results = r1.json()
            if 'result' in results['data'] and results['data']['result']:
                for metric in results['data']['result']:
                    if not metric['metric']['hash_id'] in role_hashes:
                        role_hashes[metric['metric']['hash_id']] = {'mac': metric['metric']['mac'],
                                                                    'ipv4_address': metric['metric'].get('ipv4_address', ''),
                                                                    'ipv4_os': metric['metric'].get('ipv4_os', NO_DATA),
                                                                    'timestamp': str(metric['values'][-1][0]),
                                                                    'top_role': metric['metric'].get('role', NO_DATA),
                                                                    'top_confidence': float(metric['values'][-1][1])}
        if r2:
            results = r2.json()
            if 'data' in results:
                if 'result' in results['data'] and results['data']['result']:
                    for metric in results['data']['result']:
                        if metric['metric']['hash_id'] in role_hashes:
                            role_hashes[metric['metric']['hash_id']]['second_role'] = metric['metric'].get(
                                'role', NO_DATA)
                            role_hashes[metric['metric']['hash_id']]['second_confidence'] = float(
                                metric['values'][-1][1])
        if r3:
            results = r3.json()
            if 'data' in results:
                if 'result' in results['data'] and results['data']['result']:
                    for metric in results['data']['result']:
                        if metric['metric']['hash_id'] in role_hashes:
                            role_hashes[metric['metric']['hash_id']]['third_role'] = metric['metric'].get(
                                'role', NO_DATA)
                            role_hashes[metric['metric']['hash_id']]['third_confidence'] = float(
                                metric['values'][-1][1])
        if mr:
            results = mr.json()
            if 'data' in results:
                if 'result' in results['data'] and results['data']['result']:
                    for metric in results['data']['result']:
                        if metric['metric']['hash_id'] in hashes:
                            if float(metric['values'][-1][1]) > hashes[metric['metric']['hash_id']]['latest']:
                                hashes[metric['metric']['hash_id']
                                       ] = metric['metric']
                                hashes[metric['metric']['hash_id']]['latest'] = float(
                                    metric['values'][-1][1])
                        else:
                            hashes[metric['metric']['hash_id']
                                   ] = metric['metric']
                            hashes[metric['metric']['hash_id']]['latest'] = float(
                                metric['values'][-1][1])
        return role_hashes, hashes

    def build_nodes(self):
        role_hashes, hashes = self.scrape_prometheus()
        for h in hashes:
            node = deepcopy(self.node)
            for field in hashes[h]:
                if field in node:
                    node[field] = hashes[h][field]
            if h in role_hashes:
                for field in role_hashes[h]:
                    if field in node:
                        node[field] = role_hashes[h][field]
            self.nodes.append(node)


class NetworkFull:

    @staticmethod
    def get_fields():
        return {'hash_id': NO_DATA, 'mac': 0, 'ipv4_address': 0,
                'ipv6_address': 0, 'ipv4_subnet': NO_DATA,
                'ipv6_subnet': NO_DATA, 'segment': 0, 'port': 0,
                'tenant': 0, 'next_state': NO_DATA, 'state': NO_DATA,
                'prev_state': NO_DATA, 'ignore': 'False', 'top_role': NO_DATA,
                'top_confidence': 0, 'ipv4_os': NO_DATA, 'ipv6_os': NO_DATA,
                'ipv4_rdns': NO_DATA, 'ipv6_rdns': NO_DATA,
                'ether_vendor': NO_DATA, 'controller_type': NO_DATA,
                'acls': NO_DATA}

    @staticmethod
    def get_dataset():
        fields = NetworkFull.get_fields()
        n = Nodes(fields)
        n.build_nodes()
        return n.nodes

    @staticmethod
    def on_get(_req, resp):
        network = {}
        dataset = NetworkFull.get_dataset()
        network['dataset'] = dataset

        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200


class Network:

    @staticmethod
    def get_fields():
        return {'hash_id': NO_DATA, 'mac': 0, 'ipv4_address': 0, 'ipv6_address': 0,
                'ipv4_subnet': NO_DATA, 'ipv6_subnet': NO_DATA,
                'tenant': 0, 'segment': 0, 'port': 0,
                'state': NO_DATA, 'ignore': 'False',
                'top_role': NO_DATA, 'top_confidence': 0,
                'ipv4_os': NO_DATA, 'ipv6_os': NO_DATA,
                'ipv4_rdns': NO_DATA, 'ipv6_rdns': NO_DATA,
                'ether_vendor': NO_DATA, 'controller_type': NO_DATA,
                'acls': NO_DATA}

    @staticmethod
    def field_mapping():
        return {'hash_id': 'ID', 'mac': 'MAC Address', 'segment': 'Switch',
                'port': 'Port', 'tenant': 'VLAN', 'ipv4_address': 'IPv4',
                'ipv4_subnet': 'IPv4 Subnet', 'ipv6_subnet': 'IPv6 Subnet',
                'ipv6_address': 'IPv6', 'ignore': 'Ignored', 'state': 'State',
                'next_state': 'Next State', 'prev_state': 'Previous State',
                'ipv4_os': 'IPv4 OS (p0f)', 'ipv6_os': 'IPv6 OS (p0f)',
                'top_role': 'Role (NetworkML)',
                'top_confidence': 'Role Confidence (NetworkML)',
                'ipv4_rdns': 'IPv4 rDNS',
                'ipv6_rdns': 'IPv6 rDNS', 'ether_vendor': 'Ethernet Vendor',
                'controller_type': 'SDN Controller Type',
                'acls': 'ACL History'}

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

    @staticmethod
    def on_get(_req, resp):
        network = {}
        dataset = Network.get_dataset()
        configuration = Network.get_configuration()

        network['dataset'] = dataset
        network['configuration'] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200


class NetworkByIp:

    @staticmethod
    def get_dataset(ip=None):
        fields = Network.get_fields()
        n = Nodes(fields, ip)
        n.build_nodes()
        return n.nodes

    @staticmethod
    def get_configuration():
        configuration = {'fields': []}
        for field in Network.get_fields():
            configuration['fields'].append(
                {'path': [field], 'displayName': Network.field_mapping()[field], 'groupable': 'true'})
        return configuration

    @staticmethod
    def on_get(_req, resp, ip):
        network = {}
        dataset = NetworkByIp.get_dataset(ip)
        configuration = NetworkByIp.get_configuration()

        network['dataset'] = dataset
        network['configuration'] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
