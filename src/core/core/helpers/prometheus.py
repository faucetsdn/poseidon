# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""
import datetime
import ipaddress
import logging
import re
import time
from collections import defaultdict

import requests
from poseidon_core import __version__
from poseidon_core.constants import NO_DATA
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import Endpoint
from poseidon_core.helpers.endpoint import EndpointDecoder
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Info
from prometheus_client import start_http_server
from prometheus_client import Summary


class Prometheus():

    def __init__(self):
        self.logger = logging.getLogger('prometheus')
        self.prom_metrics = {}
        self.config = Config().get_config()
        self.prometheus_addr = self.config['prometheus_ip'] + \
            ':' + self.config['prometheus_port']

    def initialize_metrics(self):
        self.prom_metrics['info'] = Info(
            'poseidon_version', 'Info about Poseidon')
        self.prom_metrics['ipv4_table'] = Gauge('poseidon_endpoint_ip_table',
                                                'IP Table',
                                                ['mac',
                                                 'tenant',
                                                 'segment',
                                                 'port',
                                                 'role',
                                                 'ipv4_os',
                                                 'hash_id'])
        self.prom_metrics['roles'] = Gauge('poseidon_endpoint_roles',
                                           'Number of endpoints by role',
                                           ['role'])
        self.prom_metrics['oses'] = Gauge('poseidon_endpoint_oses',
                                          'Number of endpoints by OS',
                                          ['ipv4_os'])
        self.prom_metrics['current_states'] = Gauge('poseidon_endpoint_current_states',
                                                    'Number of endpoints by current state',
                                                    ['current_state'])
        self.prom_metrics['vlans'] = Gauge('poseidon_endpoint_vlans',
                                           'Number of endpoints by VLAN',
                                           ['tenant'])
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
        self.prom_metrics['ncapture_count'] = Counter(
            'poseidon_ncapture_count', 'Number of times ncapture ran')
        self.prom_metrics['method_runtime_secs'] = Summary('poseidon_method_runtime_secs',
                                                           'Time spent in Monitor methods',
                                                           ['method'])
        self.prom_metrics['endpoint_role_confidence_top'] = Gauge('poseidon_role_confidence_top',
                                                                  'Confidence of top role prediction',
                                                                  ['mac',
                                                                   'name',
                                                                   'role',
                                                                   'pcap_labels',
                                                                   'ipv4_os',
                                                                   'ipv4_address',
                                                                   'ipv6_address',
                                                                   'hash_id'])
        self.prom_metrics['endpoint_role_confidence_second'] = Gauge('poseidon_role_confidence_second',
                                                                     'Confidence of second role prediction',
                                                                     ['mac',
                                                                      'name',
                                                                      'role',
                                                                      'pcap_labels',
                                                                      'ipv4_os',
                                                                      'ipv4_address',
                                                                      'ipv6_address',
                                                                      'hash_id'])
        self.prom_metrics['endpoint_role_confidence_third'] = Gauge('poseidon_role_confidence_third',
                                                                    'Confidence of third role prediction',
                                                                    ['mac',
                                                                     'name',
                                                                     'role',
                                                                     'pcap_labels',
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
                                                        'prev_state',
                                                        'next_state',
                                                        'acls',
                                                        'ignore',
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
        metrics = {'info': defaultdict(int),
                   'roles': defaultdict(int),
                   'oses': defaultdict(int),
                   'current_states': defaultdict(int),
                   'vlans': defaultdict(int),
                   'port_tenants': defaultdict(int),
                   'port_hosts': defaultdict(int),
                   'ncapture_count': 0}
        return metrics

    def update_metrics(self, hosts):

        metrics = Prometheus.get_metrics()
        metrics['info']['version'] = __version__

        for host in hosts:
            metrics['roles'][host['role']] += 1
            metrics['oses'][host['ipv4_os']] += 1
            metrics['vlans'][host['tenant']] += 1
            metrics['port_hosts'][host['port']] += 1
            metrics['port_tenants'][(host['port'], host['tenant'])] += 1
            metrics['current_states'][host['state']] += 1

        if self.prom_metrics:
            for host in hosts:
                if host['ipv4']:
                    self.prom_metrics['ipv4_table'].labels(mac=host['mac'],
                                                           tenant=host['tenant'],
                                                           segment=host['segment'],
                                                           port=host['port'],
                                                           role=host['role'],
                                                           ipv4_os=host['ipv4_os'],
                                                           hash_id=host['id']).set(int(ipaddress.ip_address(host['ipv4'])))
            for role in metrics['roles']:
                self.prom_metrics['roles'].labels(
                    role=role).set(metrics['roles'][role])
            for os_t in metrics['oses']:
                self.prom_metrics['oses'].labels(
                    ipv4_os=os_t).set(metrics['oses'][os_t])
            for current_state in metrics['current_states']:
                self.prom_metrics['current_states'].labels(current_state=current_state).set(
                    metrics['current_states'][current_state])
            for vlan in metrics['vlans']:
                self.prom_metrics['vlans'].labels(
                    tenant=vlan).set(metrics['vlans'][vlan])
            for port_tenant in metrics['port_tenants']:
                self.prom_metrics['port_tenants'].labels(port=port_tenant[0],
                                                         tenant=port_tenant[1]).set(metrics['port_tenants'][port_tenant])
            for port_host in metrics['port_hosts']:
                self.prom_metrics['port_hosts'].labels(
                    port=port_host).set(metrics['port_hosts'][port_host])
            self.prom_metrics['info'].info(metrics['info'])

    @staticmethod
    def latest_metric(metric):
        return metric['values'][-1]

    def latest_value(self, metric):
        return float(self.latest_metric(metric)[1])

    def latest_timestamp(self, metric):
        return self.latest_metric(metric)[0]

    @staticmethod
    def metric_label(metric, label, default_value=NO_DATA):
        return metric['metric'].get(label, default_value)

    def sorted_metrics(self, response):
        ''' return timeseries in order, most recently asserted, first. '''
        return sorted([
            {'metric': result['metric'], 'values': [
                self.latest_metric(result)]}
            for result in response.json()['data']['result']],
            key=lambda x: self.latest_value(x), reverse=True)

    def prom_query(self, var, start_time_str, end_time_str, step='30s'):
        payload = {'query': var, 'start': start_time_str,
                   'end': end_time_str, 'step': step}
        try:
            response = requests.get(
                'http://%s/api/v1/query_range' % self.prometheus_addr, params=payload)
        except Exception:
            return []
        return self.sorted_metrics(response)

    def consolidate_prom(self, mr, r1, r2, r3):
        hashes = {}
        if mr:
            for metric in mr:
                hash_id = self.metric_label(metric, 'hash_id')
                if hash_id not in hashes:
                    hashes[hash_id] = metric['metric']
        role_hashes = {}
        if r1:
            for metric in r1:
                hash_id = self.metric_label(metric, 'hash_id')
                if not hash_id in role_hashes:
                    role_hashes[hash_id] = {
                        'mac': self.metric_label(metric, 'mac'),
                        'top_role': self.metric_label(metric, 'role'),
                        'top_confidence': self.latest_value(metric),
                        'pcap_labels': self.metric_label(metric, 'pcap_labels', '')}
        if r2:
            for metric in r2:
                hash_id = self.metric_label(metric, 'hash_id')
                if hash_id in role_hashes:
                    role_hashes[hash_id].update({
                        'second_role': self.metric_label(metric, 'role'),
                        'second_confidence': self.latest_value(metric)})
        if r3:
            for metric in r3:
                hash_id = self.metric_label(metric, 'hash_id')
                if hash_id in role_hashes:
                    role_hashes[hash_id].update({
                        'third_role': self.metric_label(metric, 'role'),
                        'third_confidence': self.latest_value(metric)})

        return hashes, role_hashes

    def scrape_prom(self):
        current_time = datetime.datetime.utcnow()
        # 6 hours in the past and 2 hours in the future
        start_time = current_time - datetime.timedelta(hours=6)
        end_time = current_time + datetime.timedelta(hours=2)
        start_time_str = start_time.isoformat()[:-4]+'Z'
        end_time_str = end_time.isoformat()[:-4]+'Z'
        mr = self.prom_query('poseidon_endpoint_metadata',
                             start_time_str, end_time_str)
        r1 = self.prom_query(
            'poseidon_role_confidence_top{role!="%s"}' % NO_DATA, start_time_str, end_time_str)
        r2 = self.prom_query(
            'poseidon_role_confidence_second{role!="%s"}' % NO_DATA, start_time_str, end_time_str)
        r3 = self.prom_query(
            'poseidon_role_confidence_third{role!="%s"} % NO_DATA', start_time_str, end_time_str)
        return self.consolidate_prom(mr, r1, r2, r3)

    @staticmethod
    def prom_endpoints(hashes, role_hashes):
        endpoints = {}
        for p_endpoint in hashes.values():
            prev_state = p_endpoint.get('prev_state', None)
            if prev_state not in Endpoint.transitions:
                prev_state = None
            next_state = p_endpoint.get('next_state', None)
            if next_state not in Endpoint.transitions:
                next_state = None
            state = p_endpoint['state']
            p_endpoint.update({
                'name': p_endpoint['hash_id'],
                'p_next_state': next_state,
                'p_prev_state': prev_state,
                'acl_data': [],  # TODO: acl_data
                'metadata': {'mac_addresses': {}, 'ipv4_addresses': {}, 'ipv6_addresses': {}},
                'state': state,
                'ignore': False,  # TODO: force ignore off
                'endpoint_data': {
                    'mac': p_endpoint['mac'],
                    'segment': p_endpoint['segment'],
                    'port': p_endpoint['port'],
                    'vlan': p_endpoint['tenant'],
                    'tenant': p_endpoint['tenant'],
                    'ipv4': p_endpoint.get('ipv4_address', ''),
                    'ipv6': p_endpoint.get('ipv6_address', ''),
                    'controller_type': p_endpoint['controller_type'],
                    'controller': p_endpoint.get('controller', ''),
                    'name': p_endpoint['name'],
                    'ether_vendor': p_endpoint['ether_vendor'],
                    'ipv4_subnet': p_endpoint.get('ipv4_subnet', ''),
                    'ipv4_rdns': p_endpoint.get('ipv4_rdns', ''),
                    'ipv6_rdns': p_endpoint.get('ipv6_rdns', ''),
                    'ipv6_subnet': p_endpoint.get('ipv6_subnet', '')}})
            ipv4 = p_endpoint.get('ipv4_address', '')
            ipv4_os = p_endpoint.get('ipv4_os', '')
            if ipv4 and ipv4_os:
                p_endpoint['metadata']['ipv4_addresses'][ipv4] = {
                    'short_os': ipv4_os}
            mac = p_endpoint['mac']
            for role_hash in role_hashes.values():
                role_mac = role_hash['mac']
                if mac != role_mac:
                    continue
                if not mac in p_endpoint['metadata']['mac_addresses']:
                    roles = [
                        role_hash.get('top_role', NO_DATA),
                        role_hash.get('second_role', NO_DATA),
                        role_hash.get('third_role', NO_DATA)]
                    confidences = [
                        role_hash.get('top_confidence', NO_DATA),
                        role_hash.get('second_confidence', NO_DATA),
                        role_hash.get('third_confidence', NO_DATA)]
                    pcap_labels = role_hash['pcap_labels']
                    p_endpoint['metadata']['mac_addresses'][mac] = {
                        'classification': {
                            'labels': roles,
                            'confidences': confidences,
                        },
                        'pcap_labels': pcap_labels}
            endpoint = EndpointDecoder(p_endpoint).get_endpoint()
            endpoints[endpoint.name] = endpoint
        return endpoints

    def get_stored_endpoints(self):
        ''' load existing endpoints from Prometheus. '''
        hashes, role_hashes = self.scrape_prom()
        return self.prom_endpoints(hashes, role_hashes)

    def runtime_callable(self, method):
        method_name = str(method)
        method_re = re.compile(r'.+bound method (\S+).+')
        method_match = method_re.match(method_name)
        if method_match:
            method_name = method_match.group(1)
        with self.prom_metrics['method_runtime_secs'].labels(method=method_name).time():
            return method()

    def update_endpoint_metadata(self, endpoints):
        update_time = time.time()
        for hash_id, endpoint in endpoints.items():
            ipv4 = endpoint.endpoint_data['ipv4']
            ipv6 = endpoint.endpoint_data['ipv6']
            ipv4_subnet = endpoint.endpoint_data['ipv4_subnet']
            ipv6_subnet = endpoint.endpoint_data['ipv6_subnet']
            ipv4_rdns = endpoint.endpoint_data['ipv4_rdns']
            ipv6_rdns = endpoint.endpoint_data['ipv6_rdns']
            port = endpoint.endpoint_data['port']
            tenant = endpoint.endpoint_data['tenant']
            segment = endpoint.endpoint_data['segment']
            ether_vendor = endpoint.endpoint_data['ether_vendor']
            controller = endpoint.endpoint_data['controller']
            controller_type = endpoint.endpoint_data['controller_type']
            roles, confidences, pcap_labels = endpoint.get_roles_confidences_pcap_labels()
            top_role, second_role, third_role = roles
            top_conf, second_conf, third_conf = confidences
            ipv4_os = endpoint.get_ipv4_os()

            def set_prom(var, val, **prom_labels):
                prom_labels.update({
                    'mac': endpoint.endpoint_data['mac'],
                    'name': endpoint.endpoint_data['name'],
                    'hash_id': hash_id,
                })
                try:
                    self.prom_metrics[var].labels(**prom_labels).set(val)
                except ValueError:
                    pass

            def set_prom_role(var, val, role):
                set_prom(
                    var,
                    val,
                    role=role,
                    ipv4_os=ipv4_os,
                    ipv4_address=ipv4,
                    ipv6_address=ipv6,
                    pcap_labels=pcap_labels)

            def update_prom(var, **prom_labels):
                prom_labels.update({
                    'tenant': tenant,
                    'segment': segment,
                    'ether_vendor': ether_vendor,
                    'port': port,
                })
                set_prom(var, update_time, **prom_labels)

            set_prom_role(
                'endpoint_role_confidence_top',
                top_conf,
                top_role)
            set_prom_role(
                'endpoint_role_confidence_second',
                second_conf,
                second_role)
            set_prom_role(
                'endpoint_role_confidence_third',
                third_conf,
                third_role)
            update_prom(
                'endpoints',
                controller_type=controller_type,
                controller=controller)
            update_prom(
                'endpoint_state',
                state=endpoint.state)
            update_prom(
                'endpoint_os',
                ipv4_os=ipv4_os)
            update_prom(
                'endpoint_role',
                top_role=top_role)
            update_prom(
                'endpoint_ip',
                ipv4_subnet=ipv4_subnet,
                ipv6_subnet=ipv6_subnet,
                ipv4_rdns=ipv4_rdns,
                ipv6_rdns=ipv6_rdns,
                ipv4_address=ipv4,
                ipv6_address=ipv6)
            update_prom(
                'endpoint_metadata',
                prev_state=endpoint.p_prev_state,
                next_state=endpoint.p_next_state,
                acls=endpoint.acl_data,
                ignore=str(endpoint.ignore),
                ipv4_subnet=ipv4_subnet,
                ipv6_subnet=ipv6_subnet,
                ipv4_rdns=ipv4_rdns,
                ipv6_rdns=ipv6_rdns,
                controller_type=controller_type,
                controller=controller,
                state=endpoint.state,
                top_role=top_role,
                ipv4_os=ipv4_os,
                ipv4_address=ipv4,
                ipv6_address=ipv6)

    @staticmethod
    def start(port=9304):
        start_http_server(port)
