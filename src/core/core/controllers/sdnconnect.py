import difflib
import ipaddress
import json
import time
from copy import deepcopy

import pika
from poseidon_core.constants import NO_DATA
from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.controllers.faucet.faucet import FaucetProxy
from poseidon_core.helpers.actions import Actions
from poseidon_core.helpers.endpoint import Endpoint
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.helpers.endpoint import MACHINE_IP_FIELDS
from poseidon_core.helpers.endpoint import MACHINE_IP_PREFIXES
from poseidon_core.helpers.metadata import DNSResolver
from poseidon_core.helpers.metadata import get_ether_vendor
from poseidon_core.helpers.prometheus import Prometheus


class SDNConnect:

    def __init__(self, config, logger, prom, faucetconfgetsetter_cl=FaucetRemoteConfGetSetter):
        self.config = config
        self.r = None
        self.sdnc = None
        self.endpoints = {}
        self.investigations = 0
        self.coprocessing = 0
        trunk_ports = self.config['trunk_ports']
        if isinstance(trunk_ports, str):
            self.trunk_ports = json.loads(trunk_ports)
        else:
            self.trunk_ports = trunk_ports
        self.logger = logger
        self.prom = prom
        self.faucetconfgetsetter_cl = faucetconfgetsetter_cl
        self.get_sdn_context()
        self.dns_resolver = DNSResolver()
        self.get_stored_endpoints()

    def mirror_endpoint(self, endpoint):
        ''' mirror an endpoint. '''
        status = Actions(endpoint, self.sdnc).mirror_endpoint()
        if not status:
            self.logger.warning(
                'Unable to mirror the endpoint: {0}'.format(endpoint.name))

    def unmirror_endpoint(self, endpoint):
        ''' unmirror an endpoint. '''
        if endpoint.operation_active():
            status = Actions(endpoint, self.sdnc).unmirror_endpoint()
            if not status:
                self.logger.warning(
                    'Unable to unmirror the endpoint: {0}'.format(endpoint.name))
            endpoint.force_unknown()
        else:
            self.logger.info('Not unmirroring endpoint {0} in state {1}'.format(
                endpoint.name, endpoint.state))

    def clear_filters(self):
        ''' clear any exisiting filters. '''
        if isinstance(self.sdnc, FaucetProxy):
            self.sdnc.clear_mirrors()

    def default_endpoints(self):
        ''' set endpoints to default state. '''
        self.clear_filters()
        for endpoint in self.endpoints.values():
            endpoint.default()

    def get_stored_endpoints(self):
        ''' load existing endpoints from Prometheus. '''
        new_endpoints = self.prom.get_stored_endpoints()
        if new_endpoints:
            self.logger.info(
                f'Loaded {len(new_endpoints)} endpoints previously learned.')
            self.endpoints = new_endpoints

    def get_sdn_context(self):
        controller_type = self.config.get('TYPE', None)
        if controller_type == 'faucet':
            self.sdnc = FaucetProxy(
                self.config, faucetconfgetsetter_cl=self.faucetconfgetsetter_cl)
        else:
            self.logger.error(
                'Unknown SDN controller config: {0}'.format(
                    self.config))

    def not_ignored_endpoints(self, state=None):
        endpoints = [endpoint for endpoint in self.endpoints.values()
                     if not endpoint.ignore]
        if state:
            endpoints = [
                endpoint for endpoint in endpoints if endpoint.state == state]
        return endpoints

    def not_copro_ignored_endpoints(self, state=None):
        endpoints = [endpoint for endpoint in self.endpoints.values()
                     if not endpoint.copro_ignore]
        if state:
            endpoints = [
                endpoint for endpoint in endpoints if endpoint.copro_state == state]
        return endpoints

    def endpoint_by_name(self, name):
        return self.endpoints.get(name, None)

    def endpoint_by_hash(self, hash_id):
        return self.endpoint_by_name(hash_id)

    def endpoints_by_ip(self, ip):
        return [
            endpoint for endpoint in self.endpoints.values()
            if ip == endpoint.endpoint_data.get('ipv4', None) or
            ip == endpoint.endpoint_data.get('ipv6', None)]

    def endpoints_by_mac(self, mac):
        return [
            endpoint for endpoint in self.endpoints.values()
            if mac == endpoint.endpoint_data['mac']]

    def investigation_budget(self):
        self.investigations = len([
            endpoint for endpoint in self.not_ignored_endpoints()
            if endpoint.operation_active()])
        return max(
            self.config['max_concurrent_reinvestigations'] - self.investigations, 0)

    def coprocessing_budget(self):
        self.coprocessing = len([
            endpoint for endpoint in self.not_ignored_endpoints()
            if endpoint.copro_state == 'copro_coprocessing'])
        return max(
            self.config['max_concurrent_coprocessing'] - self.coprocessing, 0)

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
                    if arg == 'active':
                        endpoints.append(endpoint)
                    elif arg == 'ignored' and endpoint.ignore:
                        endpoints.append(endpoint)
                    elif endpoint.state == arg:
                        endpoints.append(endpoint)
                elif show_type in ['os', 'role']:
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
                machine['mac'], '/poseidon/src/core/core/metadata/nmap-mac-prefixes.txt')
            machine_ips.update(self._parse_machine_ip(machine))
            if 'controller_type' not in machine:
                machine.update({
                    'controller_type': 'none',
                    'controller': ''})

        if machine_ips:
            self.logger.debug('resolving %s' % machine_ips)
            resolved_machine_ips = self.dns_resolver.resolve_ips(
                list(machine_ips))
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
                m.touch()
                self.endpoints[m.name] = m
                self.logger.info(
                    'Detected new endpoint: {0}:{1}'.format(m.name, machine))
                continue

            self.merge_machine_ip(ep.endpoint_data, machine)
            if ep.endpoint_data != machine and not ep.ignore:
                diff_txt = self._diff_machine(ep.endpoint_data, machine)
                self.logger.info(
                    'Endpoint changed: {0}:{1}'.format(h, diff_txt))
                change_acls = True
                ep.endpoint_data = deepcopy(machine)
            ep.touch()

        if change_acls and self.config['AUTOMATED_ACLS']:
            status = Actions(None, self.sdnc).update_acls(
                rules_file=self.config['RULES_FILE'],
                endpoints=self.endpoints.values())
            if isinstance(status, list):
                self.logger.info(
                    'Automated ACLs did the following: {0}'.format(status[1]))
                for item in status[1]:
                    machine = {'mac': item[1],
                               'segment': item[2], 'port': item[3]}
                    h = Endpoint.make_hash(machine)
                    ep = self.endpoints.get(h, None)
                    if ep:
                        ep.acl_data.append(
                            ((item[0], item[4], item[5]), int(time.time())))

    @staticmethod
    def coprocess_endpoint(_endpoint):
        '''TODO.'''
        return

    @staticmethod
    def uncoprocess_endpoint(_endpoint):
        '''TODO'''
        return
