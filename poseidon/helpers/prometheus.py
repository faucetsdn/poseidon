# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""
import logging
import socket
from binascii import hexlify

from prometheus_client import Gauge
from prometheus_client import start_http_server


class Prometheus():

    def __init__(self):
        self.logger = logging.getLogger('prometheus')
        self.prom_metrics = {}

    def initialize_metrics(self):
        self.prom_metrics['inactive'] = Gauge('poseidon_endpoint_inactive',
                                              'Number of endpoints that are inactive')
        self.prom_metrics['active'] = Gauge('poseidon_endpoint_active',
                                            'Number of endpoints that are active')
        self.prom_metrics['behavior'] = Gauge('poseidon_endpoint_behavior',
                                              'Behavior of an endpoint, 0 is normal, 1 is abnormal',
                                              ['ipv4',
                                               'mac',
                                               'tenant',
                                               'segment',
                                               'port',
                                               'role',
                                               'os',
                                               'source'])
        self.prom_metrics['ipv4_table'] = Gauge('poseidon_endpoint_ip_table',
                                                'IP Table',
                                                ['mac',
                                                 'tenant',
                                                 'segment',
                                                 'port',
                                                 'role',
                                                 'os',
                                                 'id',
                                                 'source'])
        self.prom_metrics['roles'] = Gauge('poseidon_endpoint_roles',
                                           'Number of endpoints by role',
                                           ['source',
                                            'role'])
        self.prom_metrics['oses'] = Gauge('poseidon_endpoint_oses',
                                          'Number of endpoints by OS',
                                          ['source',
                                           'os'])
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

    @staticmethod
    def get_metrics():
        metrics = {'roles': {},
                   'oses': {},
                   'current_states': {('Poseidon', 'known'): 0,
                                      ('Poseidon', 'unknown'): 0,
                                      ('Poseidon', 'inactive'): 0,
                                      ('Poseidon', 'mirroring'): 0,
                                      ('Poseidon', 'shutdown'): 0,
                                      ('Poseidon', 'queued'): 0,
                                      ('Poseidon', 'abnormal'): 0,
                                      ('Poseidon', 'reinvestigating'): 0},
                   'vlans': {},
                   'sources': {},
                   'port_tenants': {},
                   'port_hosts': {},
                   'inactives': 0,
                   'actives': 0}
        return metrics

    def update_metrics(self, hosts):

        def ip2int(ip):
            ''' convert ip quad octet string to an int '''
            if ip in [None, 'None', '::']:
                res = 0
            elif ':' in ip:
                res = int(hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)
            else:
                o = list(map(int, ip.split('.')))
                res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
            return res

        metrics = Prometheus.get_metrics()
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
                    self.prom_metrics['behavior'].labels(ip=host['ipv4'],
                                                         mac=host['mac'],
                                                         tenant=host['tenant'],
                                                         segment=host['segment'],
                                                         port=host['port'],
                                                         role=host['role'],
                                                         os=host['ipv4_os'],
                                                         source=host['source']).set(host['behavior'])
                    self.prom_metrics['ipv4_table'].labels(mac=host['mac'],
                                                           tenant=host['tenant'],
                                                           segment=host['segment'],
                                                           port=host['port'],
                                                           role=host['role'],
                                                           os=host['ipv4_os'],
                                                           id=host['id'],
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
                                                 os=os_t[1]).set(metrics['oses'][os_t])
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
            self.prom_metrics['inactive'].set(metrics['inactives'])
            self.prom_metrics['active'].set(metrics['actives'])
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'unable to send results to prometheus because {0}'.format(str(e)))

    @staticmethod
    def start(port=9304):
        start_http_server(port)
