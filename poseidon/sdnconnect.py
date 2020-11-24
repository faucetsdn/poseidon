#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ipaddress
import json
import time
from copy import deepcopy

import difflib
import pika

from poseidon.constants import NO_DATA
from poseidon.controllers.faucet.faucet import FaucetProxy
from poseidon.helpers.actions import Actions
from poseidon.helpers.endpoint import Endpoint
from poseidon.helpers.endpoint import endpoint_factory
from poseidon.helpers.endpoint import MACHINE_IP_FIELDS
from poseidon.helpers.endpoint import MACHINE_IP_PREFIXES
from poseidon.helpers.metadata import get_ether_vendor
from poseidon.helpers.metadata import DNSResolver
from poseidon.helpers.redis import PoseidonRedisClient


class SDNConnect:

    def __init__(self, controller, logger, first_time=True):
        self.controller = controller
        self.r = None
        self.first_time = first_time
        self.sdnc = None
        self.endpoints = {}
        trunk_ports = self.controller['trunk_ports']
        if isinstance(trunk_ports, str):
            self.trunk_ports = json.loads(trunk_ports)
        else:
            self.trunk_ports = trunk_ports
        self.logger = logger
        self.get_sdn_context()
        self.prc = PoseidonRedisClient(self.logger)
        self.prc.connect()
        self.dns_resolver = DNSResolver()
        if self.first_time:
            self.endpoints = {}
            self.investigations = 0
            self.coprocessing = 0
            self.clear_filters()
            self.default_endpoints()

    def mirror_endpoint(self, endpoint):
        ''' mirror an endpoint. '''
        status = Actions(endpoint, self.sdnc).mirror_endpoint()
        if status:
            self.prc.inc_network_tools_counts()
        else:
            self.logger.warning(
                'Unable to mirror the endpoint: {0}'.format(endpoint.name))

    def unmirror_endpoint(self, endpoint):
        ''' unmirror an endpoint. '''
        status = Actions(endpoint, self.sdnc).unmirror_endpoint()
        if not status:
            self.logger.warning(
                'Unable to unmirror the endpoint: {0}'.format(endpoint.name))

    def clear_filters(self):
        ''' clear any exisiting filters. '''
        if isinstance(self.sdnc, FaucetProxy):
            self.sdnc.clear_mirrors()

    def default_endpoints(self):
        ''' set endpoints to default state. '''
        self.get_stored_endpoints()
        for endpoint in self.endpoints.values():
            endpoint.default()
        self.store_endpoints()

    def get_stored_endpoints(self):
        ''' load existing endpoints from Redis. '''
        new_endpoints = self.prc.get_stored_endpoints()
        if new_endpoints:
            self.endpoints = new_endpoints

    def get_sdn_context(self):
        controller_type = self.controller.get('TYPE', None)
        if controller_type == 'faucet':
            self.sdnc = FaucetProxy(self.controller)
        elif controller_type == 'None':
            self.sdnc = None
        else:
            self.logger.error(
                'Unknown SDN controller config: {0}'.format(
                    self.controller))

    def endpoint_by_name(self, name):
        return self.endpoints.get(name, None)

    def endpoint_by_hash(self, hash_id):
        return self.endpoint_by_name(hash_id)

    def endpoints_by_ip(self, ip):
        endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if ip == endpoint.endpoint_data.get('ipv4', None) or
            ip == endpoint.endpoint_data.get('ipv6', None)]
        return endpoints

    def endpoints_by_mac(self, mac):
        endpoints = [
            endpoint for endpoint in self.endpoints.values()
            if mac == endpoint.endpoint_data['mac']]
        return endpoints

    @staticmethod
    def _connect_rabbit():
        # Rabbit settings
        exchange = 'topic-poseidon-internal'
        exchange_type = 'topic'

        # Starting rabbit connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='RABBIT_SERVER')
        )

        channel = connection.channel()
        channel.exchange_declare(
            exchange=exchange, exchange_type=exchange_type
        )

        return channel, exchange, connection

    @staticmethod
    def publish_action(action, message):
        try:
            channel, exchange, connection = SDNConnect._connect_rabbit()
            channel.basic_publish(exchange=exchange,
                                  routing_key=action,
                                  body=message)
            connection.close()
        except Exception as e:  # pragma: no cover
            print(str(e))

    def show_endpoints(self, arg):
        endpoints = []
        if arg == 'all':
            endpoints = list(self.endpoints.values())
        else:
            show_type, arg = arg.split(' ', 1)
            for endpoint in self.endpoints.values():
                if show_type == 'state':
                    if arg == 'active' and endpoint.state != 'inactive':
                        endpoints.append(endpoint)
                    elif arg == 'ignored' and endpoint.ignore:
                        endpoints.append(endpoint)
                    elif endpoint.state == arg:
                        endpoints.append(endpoint)
                elif show_type in ['os', 'behavior', 'role']:
                    mac_addresses = endpoint.metadata.get(
                        'mac_addresses', None)
                    endpoint_mac = endpoint.endpoint_data['mac']
                    if endpoint_mac and mac_addresses and endpoint_mac in mac_addresses:
                        timestamps = mac_addresses[endpoint_mac]
                        try:
                            newest = sorted(
                                [timestamp for timestamp in timestamps])[-1]
                            newest = timestamps[newest]
                        except IndexError:
                            newest = None
                        if newest:
                            if 'labels' in newest:
                                if arg.replace('-', ' ') == newest['labels'][0].lower():
                                    endpoints.append(endpoint)
                            if 'behavior' in newest:
                                if arg == newest['behavior'].lower():
                                    endpoints.append(endpoint)

                    # filter by operating system
                    for ip_field in MACHINE_IP_FIELDS:
                        ip_addresses_field = '_'.join((ip_field, 'addresses'))
                        ip_addresses = endpoint.metadata.get(
                            ip_addresses_field, None)
                        machine_ip = endpoint.endpoint_data.get(ip_field, None)
                        if machine_ip and ip_addresses and machine_ip in ip_addresses:
                            metadata = ip_addresses[machine_ip]
                            os = metadata.get('os', None)
                            if os and os.lower() == arg:
                                endpoints.append(endpoint)
        return endpoints

    def check_endpoints(self, messages):
        if not self.sdnc:
            return

        current = None
        parsed = None

        try:
            current = self.sdnc.get_endpoints(messages=messages)
            parsed = self.sdnc.format_endpoints(current)
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Could not establish connection to controller because {0}.'.format(e))

        self.find_new_machines(parsed)

    @staticmethod
    def _diff_machine(machine_a, machine_b):

        def _machine_strlines(machine):
            return str(json.dumps(machine, indent=2)).splitlines()

        machine_a_strlines = _machine_strlines(machine_a)
        machine_b_strlines = _machine_strlines(machine_b)
        return '\n'.join(difflib.unified_diff(
            machine_a_strlines, machine_b_strlines, n=1))

    @staticmethod
    def _parse_machine_ip(machine):
        machine_ips = set()
        machine_ip_data = {}
        for ip_field, fields in MACHINE_IP_FIELDS.items():
            try:
                raw_field = machine.get(ip_field, None)
                machine_ip = str(ipaddress.ip_address(raw_field))
                machine_subnet = str(ipaddress.ip_network(machine_ip).supernet(
                    new_prefix=MACHINE_IP_PREFIXES[ip_field]))
            except ValueError:
                machine_ip = None
                machine_subnet = None
            machine_ip_data[ip_field] = ''
            if machine_ip:
                machine_ips.add(machine_ip)
                machine_ip_data.update({
                    ip_field: machine_ip,
                    '_'.join((ip_field, 'subnet')): machine_subnet})
            for field in fields:
                if field not in machine_ip_data:
                    machine_ip_data[field] = NO_DATA
        machine.update(machine_ip_data)
        return machine_ips

    @staticmethod
    def _update_machine_rdns(machine, resolved_machine_ips):
        for ip_field in MACHINE_IP_FIELDS:
            rdns_field = '_'.join((ip_field, 'rdns'))
            machine_ip = machine[ip_field]
            resolved_ip = resolved_machine_ips.get(machine_ip, machine_ip)
            machine[rdns_field] = resolved_ip

    @staticmethod
    def merge_machine_ip(old_machine, new_machine):
        for ip_field, fields in MACHINE_IP_FIELDS.items():
            ip = new_machine.get(ip_field, None)
            old_ip = old_machine.get(ip_field, None)
            if not ip and old_ip:
                new_machine[ip_field] = old_ip
                for field in fields:
                    if field in old_machine:
                        new_machine[field] = old_machine[field]

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''

        change_acls = False
        machine_ips = set()

        for machine in machines:
            machine['ether_vendor'] = get_ether_vendor(
                machine['mac'], '/poseidon/poseidon/metadata/nmap-mac-prefixes.txt')
            machine_ips.update(self._parse_machine_ip(machine))
            if 'controller_type' not in machine:
                machine.update({
                    'controller_type': 'none',
                    'controller': ''})

        if machine_ips:
            self.logger.debug('resolving %s' % machine_ips)
            resolved_machine_ips = self.dns_resolver.resolve_ips(list(machine_ips))
            self.logger.debug('resolver results %s', resolved_machine_ips)
            for machine in machines:
                self._update_machine_rdns(machine, resolved_machine_ips)

        for machine in machines:
            trunk = False
            for sw in self.trunk_ports:
                if sw == machine['segment'] and self.trunk_ports[sw].split(',')[1] == str(machine['port']) and self.trunk_ports[sw].split(',')[0] == machine['mac']:
                    trunk = True

            h = Endpoint.make_hash(machine, trunk=trunk)
            ep = self.endpoints.get(h, None)
            if ep is None:
                change_acls = True
                m = endpoint_factory(h)
                m.endpoint_data = deepcopy(machine)
                self.endpoints[m.name] = m
                self.logger.info(
                    'Detected new endpoint: {0}:{1}'.format(m.name, machine))
            else:
                self.merge_machine_ip(ep.endpoint_data, machine)

            if ep and ep.endpoint_data != machine and not ep.ignore:
                diff_txt = self._diff_machine(ep.endpoint_data, machine)
                self.logger.info(
                    'Endpoint changed: {0}:{1}'.format(h, diff_txt))
                change_acls = True
                ep.endpoint_data = deepcopy(machine)
                if ep.state == 'inactive' and machine['active'] == 1:
                    ep.reactivate()
                elif ep.state != 'inactive' and machine['active'] == 0:
                    if ep.state in ['mirroring', 'reinvestigating']:
                        self.unmirror_endpoint(ep)
                        if ep.state == 'mirroring':
                            ep.p_next_state = 'mirror'
                        elif ep.state == 'reinvestigating':
                            ep.p_next_state = 'reinvestigate'
                    if ep.state in ['known', 'abnormal']:
                        ep.p_next_state = ep.state
                    ep.inactive()  # pytype: disable=attribute-error

        if change_acls and self.controller['AUTOMATED_ACLS']:
            status = Actions(None, self.sdnc).update_acls(
                rules_file=self.controller['RULES_FILE'],
                endpoints=self.endpoints.values())
            if isinstance(status, list):
                self.logger.info(
                    'Automated ACLs did the following: {0}'.format(status[1]))
                for item in status[1]:
                    machine = {'mac': item[1], 'segment': item[2], 'port': item[3]}
                    h = Endpoint.make_hash(machine)
                    ep = self.endpoints.get(h, None)
                    if ep:
                        ep.acl_data.append(
                            ((item[0], item[4], item[5]), int(time.time())))
        self.refresh_endpoints()

    def store_endpoints(self):
        ''' store current endpoints in Redis. '''
        self.prc.store_endpoints(self.endpoints)

    def refresh_endpoints(self):
        self.logger.debug('refresh endpoints')
        self.store_endpoints()
        self.get_stored_endpoints()
