# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""
import datetime
import logging
import requests
import socket
from binascii import hexlify

from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Info
from prometheus_client import Summary
from prometheus_client import start_http_server


class Prometheus():

    def __init__(self):
        self.logger = logging.getLogger('prometheus')
        self.prom_metrics = {}

    def initialize_metrics(self):
        self.prom_metrics['info'] = Info('poseidon_version', 'Info about Poseidon')
        self.prom_metrics['inactive'] = Gauge('poseidon_endpoint_inactive',
                                              'Number of endpoints that are inactive')
        self.prom_metrics['active'] = Gauge('poseidon_endpoint_active',
                                            'Number of endpoints that are active')
        self.prom_metrics['ipv4_table'] = Gauge('poseidon_endpoint_ip_table',
                                                'IP Table',
                                                ['mac',
                                                 'tenant',
                                                 'segment',
                                                 'port',
                                                 'role',
                                                 'ipv4_os',
                                                 'hash_id',
                                                 'source'])
        self.prom_metrics['roles'] = Gauge('poseidon_endpoint_roles',
                                           'Number of endpoints by role',
                                           ['source',
                                            'role'])
        self.prom_metrics['oses'] = Gauge('poseidon_endpoint_oses',
                                          'Number of endpoints by OS',
                                          ['source',
                                           'ipv4_os'])
        self.prom_metrics['current_states'] = Gauge('poseidon_endpoint_current_states',
                                                    'Number of endpoints by current state',
                                                    ['source',
                                                     'current_state'])
        self.prom_metrics['vlans'] = Gauge('poseidon_endpoint_vlans',
                                           'Number of endpoints by VLAN',
                                           ['source',
                                            'tenant'])
        self.prom_metrics['sources'] = Gauge('poseidon_endpoint_sources',
                                             'Number of endpoints by record source',
                                             ['source'])
        self.prom_metrics['port_tenants'] = Gauge('poseidon_endpoint_port_tenants',
                                                  'Number of tenants by port',
                                                  ['port',
                                                   'tenant'])
        self.prom_metrics['port_hosts'] = Gauge('poseidon_endpoint_port_hosts',
                                                'Number of hosts by port',
                                                ['port'])
        self.prom_metrics['last_rabbitmq_routing_key_time'] = Gauge('poseidon_last_rabbitmq_routing_key_time',
                                                                    'Epoch time when last received a RabbitMQ message',
                                                                    ['routing_key'])
        self.prom_metrics['ncapture_count'] = Counter('poseidon_ncapture_count', 'Number of times ncapture ran')
        self.prom_metrics['monitor_runtime_secs'] = Summary('poseidon_monitor_runtime_secs',
                                                            'Time spent in Monitor methods',
                                                            ['method'])
        self.prom_metrics['endpoint_role_confidence_top'] = Gauge('poseidon_role_confidence_top',
                                                                  'Confidence of top role prediction',
                                                                  ['mac',
                                                                   'name',
                                                                   'role',
                                                                   'ipv4_os',
                                                                   'ipv4_address',
                                                                   'ipv6_address',
                                                                   'hash_id'])
        self.prom_metrics['endpoint_role_confidence_second'] = Gauge('poseidon_role_confidence_second',
                                                                  'Confidence of second role prediction',
                                                                  ['mac',
                                                                   'name',
                                                                   'role',
                                                                   'ipv4_os',
                                                                   'ipv4_address',
                                                                   'ipv6_address',
                                                                   'hash_id'])
        self.prom_metrics['endpoint_role_confidence_third'] = Gauge('poseidon_role_confidence_third',
                                                                  'Confidence of third role prediction',
                                                                  ['mac',
                                                                   'name',
                                                                   'role',
                                                                   'ipv4_os',
                                                                   'ipv4_address',
                                                                   'ipv6_address',
                                                                   'hash_id'])
        self.prom_metrics['endpoints'] = Gauge('poseidon_endpoints',
                                               'All endpoints',
                                               ['mac',
                                                'tenant',
                                                'segment',
                                                'ether_vendor',
                                                'controller_type',
                                                'controller',
                                                'name',
                                                'port',
                                                'hash_id'])
        self.prom_metrics['endpoint_state'] = Gauge('poseidon_endpoint_state',
                                                    'State for all endpoints',
                                                    ['mac',
                                                     'tenant',
                                                     'segment',
                                                     'ether_vendor',
                                                     'name',
                                                     'port',
                                                     'state',
                                                     'hash_id'])
        self.prom_metrics['endpoint_os'] = Gauge('poseidon_endpoint_os',
                                                 'Operating System for all endpoints',
                                                 ['mac',
                                                  'tenant',
                                                  'segment',
                                                  'ether_vendor',
                                                  'name',
                                                  'port',
                                                  'ipv4_os',
                                                  'hash_id'])
        self.prom_metrics['endpoint_role'] = Gauge('poseidon_endpoint_role',
                                                 'Top role for all endpoints',
                                                 ['mac',
                                                  'tenant',
                                                  'segment',
                                                  'ether_vendor',
                                                  'name',
                                                  'port',
                                                  'top_role',
                                                  'hash_id'])
        self.prom_metrics['endpoint_ip'] = Gauge('poseidon_endpoint_ip',
                                                 'IP Address for all endpoints',
                                                 ['mac',
                                                  'tenant',
                                                  'segment',
                                                  'ether_vendor',
                                                  'name',
                                                  'port',
                                                  'ipv4_address',
                                                  'ipv6_address',
                                                  'ipv4_subnet',
                                                  'ipv6_subnet',
                                                  'ipv4_rdns',
                                                  'ipv6_rdns',
                                                  'hash_id'])
        self.prom_metrics['endpoint_metadata'] = Gauge('poseidon_endpoint_metadata',
                                                       'Metadata for all endpoints',
                                                       ['mac',
                                                        'tenant',
                                                        'segment',
                                                        'ether_vendor',
                                                        'next_state',
                                                        'ignore',
                                                        'active',
                                                        'ipv4_subnet',
                                                        'ipv6_subnet',
                                                        'ipv4_rdns',
                                                        'ipv6_rdns',
                                                        'controller_type',
                                                        'controller',
                                                        'name',
                                                        'state',
                                                        'port',
                                                        'top_role',
                                                        'ipv4_os',
                                                        'ipv4_address',
                                                        'ipv6_address',
                                                        'hash_id'])

    @staticmethod
    def get_metrics():
        metrics = {'info': {},
                   'roles': {},
                   'oses': {},
                   'current_states': {('Poseidon', 'known'): 0,
                                      ('Poseidon', 'unknown'): 0,
                                      ('Poseidon', 'inactive'): 0,
                                      ('Poseidon', 'mirroring'): 0,
                                      ('Poseidon', 'shutdown'): 0,
                                      ('Poseidon', 'queued'): 0,
                                      ('Poseidon', 'reinvestigating'): 0},
                   'vlans': {},
                   'sources': {},
                   'port_tenants': {},
                   'port_hosts': {},
                   'inactives': 0,
                   'actives': 0,
                   'ncapture_count': 0}
        return metrics

    def update_metrics(self, hosts):

        def ip2int(ip):
            ''' convert ip quad octet string to an int '''
            if not ip or ip in ['None', '::']:
                res = 0
            elif ':' in ip:
                res = int(hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)
            else:
                o = list(map(int, ip.split('.')))
                res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
            return res

        metrics = Prometheus.get_metrics()

        # get version
        try:
            with open('/poseidon/VERSION', 'r') as f:  # pragma: no cover
                for line in f:
                    metrics['info']['version'] = line.strip()
        except Exception as e:
            print('Unable to get version from the version file')

        for host in hosts:
            if host['active'] == 0:
                metrics['inactives'] += 1
            if host['active'] == 1:
                metrics['actives'] += 1
            if (host['source'], host['role']) in metrics['roles']:
                if host['active'] == 1:
                    metrics['roles'][(host['source'],
                                      host['role'])] += 1
            else:
                if host['active'] == 1:
                    metrics['roles'][(host['source'], host['role'])] = 1
                else:
                    metrics['roles'][(host['source'], host['role'])] = 0

            if (host['source'], host['ipv4_os']) in metrics['oses']:
                if host['active'] == 1:
                    metrics['oses'][(host['source'], host['ipv4_os'])] += 1
            else:
                if host['active'] == 1:
                    metrics['oses'][(host['source'], host['ipv4_os'])] = 1
                else:
                    metrics['oses'][(host['source'], host['ipv4_os'])] = 0

            if (host['source'], host['state']) in metrics['current_states']:
                if host['active'] == 1:
                    metrics['current_states'][(host['source'],
                                               host['state'])] += 1
            else:
                if host['active'] == 1:
                    metrics['current_states'][(host['source'],
                                               host['state'])] = 1
                else:
                    metrics['current_states'][(host['source'],
                                               host['state'])] = 0

            if (host['source'], host['tenant']) in metrics['vlans']:
                if host['active'] == 1:
                    metrics['vlans'][(host['source'],
                                      host['tenant'])] += 1
            else:
                if host['active'] == 1:
                    metrics['vlans'][(host['source'],
                                      host['tenant'])] = 1
                else:
                    metrics['vlans'][(host['source'],
                                      host['tenant'])] = 0

            if (host['source']) in metrics['sources']:
                if host['active'] == 1:
                    metrics['sources'][(host['source'])] += 1
            else:
                if host['active'] == 1:
                    metrics['sources'][(host['source'])] = 1
                else:
                    metrics['sources'][(host['source'])] = 0

            if (host['port'], host['tenant']) in metrics['port_tenants']:
                if host['active'] == 1:
                    metrics['port_tenants'][(
                        host['port'], host['tenant'])] += 1
            else:
                if host['active'] == 1:
                    metrics['port_tenants'][(host['port'], host['tenant'])] = 1
                else:
                    metrics['port_tenants'][(host['port'], host['tenant'])] = 0

            if (host['port']) in metrics['port_hosts']:
                if host['active'] == 1:
                    metrics['port_hosts'][(host['port'])] += 1
            else:
                if host['active'] == 1:
                    metrics['port_hosts'][(host['port'])] = 1
                else:
                    metrics['port_hosts'][(host['port'])] = 0

            try:
                if host['active'] == 1:
                    self.prom_metrics['ipv4_table'].labels(mac=host['mac'],
                                                           tenant=host['tenant'],
                                                           segment=host['segment'],
                                                           port=host['port'],
                                                           role=host['role'],
                                                           ipv4_os=host['ipv4_os'],
                                                           hash_id=host['id'],
                                                           source=host['source']).set(ip2int(host['ipv4']))
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Unable to send {0} results to prometheus because {1}'.format(host, str(e)))

        try:
            for role in metrics['roles']:
                self.prom_metrics['roles'].labels(source=role[0],
                                                  role=role[1]).set(metrics['roles'][role])
            for os_t in metrics['oses']:
                self.prom_metrics['oses'].labels(source=os_t[0],
                                                 ipv4_os=os_t[1]).set(metrics['oses'][os_t])
            for current_state in metrics['current_states']:
                self.prom_metrics['current_states'].labels(source=current_state[0],
                                                           current_state=current_state[1]).set(metrics['current_states'][current_state])
            for vlan in metrics['vlans']:
                self.prom_metrics['vlans'].labels(source=vlan[0],
                                                  tenant=vlan[1]).set(metrics['vlans'][vlan])
            for source in metrics['sources']:
                self.prom_metrics['sources'].labels(source=source).set(
                    metrics['sources'][source])
            for port_tenant in metrics['port_tenants']:
                self.prom_metrics['port_tenants'].labels(port=port_tenant[0],
                                                         tenant=port_tenant[1]).set(metrics['port_tenants'][port_tenant])
            for port_host in metrics['port_hosts']:
                self.prom_metrics['port_hosts'].labels(
                    port=port_host).set(metrics['port_hosts'][port_host])
            self.prom_metrics['info'].info(metrics['info'])
            self.prom_metrics['inactive'].set(metrics['inactives'])
            self.prom_metrics['active'].set(metrics['actives'])
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Unable to send results to prometheus because {0}'.format(str(e)))

    def get_stored_endpoints(self):
        ''' load existing endpoints from Prometheus. '''
        endpoints = {}
        r = None
        current_time = datetime.datetime.utcnow()
        start_time = current_time - datetime.timedelta(hours=6)
        end_time = current_time + datetime.timedelta(hours=2)
        start_time_str = start_time.isoformat()[:-4]+"Z"
        end_time_str = end_time.isoformat()[:-4]+"Z"
        try:
            payload = {'query': 'poseidon_endpoint_metadata', 'start': start_time_str, 'end': end_time_str, 'step': '30s'}
            # hardcoded endpoint ok because Docker networking
            r = requests.get('http://prometheus:9090/api/v1/query_range', params=payload)

        except Exception as e:
            self.logger.error(f'Unable to get endpoints from Prometheus because: {e}')
        if r:
            results = r.json()
            if 'data' in results:
                if 'result' in results['data'] and results['data']['result']:
                    hashes = {}
                    for metric in results['data']['result']:
                        if metric['metric']['hash_id'] in hashes:
                            if float(metric['values'][-1][1]) > hashes[metric['metric']['hash_id']]['latest']:
                                hashes[metric['metric']['hash_id']] = metric['metric']
                                hashes[metric['metric']['hash_id']]['latest'] = float(metric['values'][-1][1])
                        else:
                            hashes[metric['metric']['hash_id']] = metric['metric']
                            hashes[metric['metric']['hash_id']]['latest'] = float(metric['values'][-1][1])
                    # TODO
                    # format hash metrics into endpoints
            else:
                self.logger.error(f'Bad request: {results}')
        return endpoints


    @staticmethod
    def start(port=9304):
        start_http_server(port)
