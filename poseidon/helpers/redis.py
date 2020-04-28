import ast
import ipaddress
import time
from redis import StrictRedis

from poseidon.helpers.endpoint import EndpointDecoder
from poseidon.helpers.endpoint import HistoryTypes
from poseidon.helpers.endpoint import MACHINE_IP_FIELDS
from poseidon.helpers.endpoint import MACHINE_IP_PREFIXES


class PoseidonRedisClient:

    def __init__(self, logger, host='redis', port=6379, db=0):
        self.logger = logger
        self.host = host
        self.port = port
        self.db = 0
        self.r = None

    def connect(self):
        try:
            self.r = StrictRedis(
                host=self.host, port=self.port, db=self.db,
                socket_connect_timeout=30,
                socket_timeout=30,
                socket_keepalive=True)
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Failed connect to Redis because: {0}'.format(str(e)))

    def hmset(self, key, values):
        str_values = {str(k): str(v) for k, v in values.items()}
        self.logger.debug('store key %s value %s', key, str_values)
        self.r.hmset(key, str_values)

    def store_p0f_result(self, my_obj):
        # TODO: migrate to store_tool_result()
        try:
            data = my_obj['data']
        except KeyError:
            return
        if not data:
            return
        if self.r:
            for ip, ip_data in data.items():
                self.hmset(str(ip), ip_data)

    def store_tool_result(self, my_obj, tool):
        if self.r:
            try:
                data = my_obj['data']
            except KeyError:
                return
            if not data:
                return
            for poseidon_hash, results in data.items():
                if not isinstance(results, dict):
                    continue
                if not results.get('valid', False):
                    continue
                source_mac = results['source_mac']
                timestamp = time.time()
                key = '_'.join((tool, source_mac, str(timestamp)))
                redis_results = {poseidon_hash: results}
                self.hmset(key, redis_results)
                update_list = []
                try:
                    updates = self.r.hgetall(source_mac)
                    update_list = ast.literal_eval(
                        updates[b'timestamps'].decode('ascii'))
                except KeyError:
                    pass
                update_list.append(timestamp)
                update_list = sorted(update_list)
                redis_times = {'timestamps': update_list}
                self.hmset(source_mac, redis_times)

    def get_stored_endpoints(self):
        ''' load existing endpoints from Redis. '''
        if self.r:
            try:
                p_endpoints = self.r.get('p_endpoints')
                if p_endpoints:
                    new_endpoints = {}
                    p_endpoints = ast.literal_eval(
                        p_endpoints.decode('ascii'))
                    for p_endpoint in p_endpoints:
                        endpoint = EndpointDecoder(
                            p_endpoint).get_endpoint()
                        new_endpoints[endpoint.name] = endpoint
                    return new_endpoints
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Unable to get existing endpoints from Redis because {0}'.format(str(e)))
        return {}

    @staticmethod
    def parse_metadata(mac_info, ml_info):
        metadata = {}
        tmp = {}
        if mac_info[b'poseidon_hash'] in ml_info:
            tmp = ast.literal_eval(
                ml_info[mac_info[b'poseidon_hash']].decode('ascii'))
        elif mac_info[b'poseidon_hash'].decode('ascii') in ml_info:
            tmp = ast.literal_eval(
                ml_info[mac_info[b'poseidon_hash'].decode('ascii')].decode('ascii'))
        classification = tmp.get('classification', {})
        for ml_field in ('labels', 'confidences'):
            content = classification.get(ml_field, [])
            metadata[ml_field] = content
        behavior = 'None'
        pcap_labels = 'None'
        if 'decisions' in tmp:
            decisions = tmp['decisions']
            if 'behavior' in decisions:
                behavior = decisions['behavior']
        if 'pcap_labels' in tmp:
            pcap_labels = tmp['pcap_labels']
        metadata.update({
            'behavior': behavior,
            'pcap_labels': pcap_labels})
        return metadata

    def get_stored_metadata(self, hash_id):
        mac_addresses = {}
        ip_addresses = {ip_field: {} for ip_field in MACHINE_IP_FIELDS}

        if self.r:
            macs = []
            try:
                macs = self.r.smembers('mac_addresses')
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Unable to get existing mac addresses from Redis because: {0}'.format(str(e)))
            for mac in macs:
                try:
                    mac_info = self.r.hgetall(mac)
                    if b'poseidon_hash' in mac_info and mac_info[b'poseidon_hash'] == hash_id.encode('utf-8'):
                        source_mac = mac.decode('ascii')
                        mac_addresses[source_mac] = {}
                        if b'timestamps' in mac_info:
                            raw_timestamps = mac_info[b'timestamps']
                            try:
                                timestamps = ast.literal_eval(
                                    raw_timestamps.decode('ascii'))
                                for timestamp in timestamps:
                                    key = '_'.join(('networkml', source_mac, str(timestamp)))
                                    ml_info = self.r.hgetall(key)
                                    metadata = self.parse_metadata(
                                        mac_info, ml_info)
                                    mac_addresses[source_mac][str(
                                        timestamp)] = metadata
                                    self.logger.debug('got ML data %s from %s, %s', metadata, ml_info, mac_info)
                            except Exception as e:  # pragma: no cover
                                self.logger.error(
                                    'Unable to get existing ML data from Redis because: {0} (raw_timestamps {1})'.format(
                                        str(e), str(raw_timestamps)))
                        try:
                            poseidon_info = self.r.hgetall(
                                mac_info[b'poseidon_hash'])
                            if b'endpoint_data' in poseidon_info:
                                endpoint_data = ast.literal_eval(
                                    poseidon_info[b'endpoint_data'].decode('ascii'))
                                for ip_field in MACHINE_IP_FIELDS:
                                    try:
                                        raw_field = endpoint_data.get(
                                            ip_field, None)
                                        machine_ip = ipaddress.ip_address(
                                            raw_field)
                                    except ValueError:
                                        machine_ip = ''
                                    if machine_ip:
                                        # TODO: migrate to networkml-style results rather than just raw IP lookup.
                                        try:
                                            ip_info = self.r.hgetall(raw_field)
                                            short_os = ip_info.get(
                                                b'short_os', None)
                                            ip_addresses[ip_field][raw_field] = {
                                            }
                                            if short_os:
                                                ip_addresses[ip_field][raw_field]['os'] = short_os.decode(
                                                    'ascii')
                                        except Exception as e:  # pragma: no cover
                                            self.logger.error(
                                                'Unable to get existing {0} data from Redis because: {1}'.format(ip_field, str(e)))
                        except Exception as e:  # pragma: no cover
                            self.logger.error(
                                'Unable to get existing endpoint data from Redis because: {0}'.format(str(e)))
                except Exception as e:  # pragma: no cover
                    self.logger.error(
                        'Unable to get existing metadata for {0} from Redis because: {1}'.format(mac, str(e)))
        return mac_addresses, ip_addresses['ipv4'], ip_addresses['ipv6']

    @staticmethod
    def update_history(endpoint, mac_addresses, ipv4_addresses, ipv6_addresses):
        # list of fields to make history entries for, along with entry type for that field
        fields = [
            {'field_name': 'behavior', 'entry_type': HistoryTypes.PROPERTY_CHANGE},
            {'field_name': 'ipv4_OS', 'entry_type': HistoryTypes.PROPERTY_CHANGE},
            {'field_name': 'ipv6_OS', 'entry_type': HistoryTypes.PROPERTY_CHANGE},
        ]
        # make history entries for any changed prop
        prior = None
        for record in mac_addresses.values():
            for field in fields:
                if field['field_name'] in record and prior and field['field_name'] in prior and \
                   prior[field['field_name']] != record[field['field_name']]:
                    endpoint.update_property_history(field['entry_type'], field['field_name'], endpoint.endpoint_data.mac_addresses['field_name'],
                                                     prior[field['field_name']], record[field['field_name']])
                prior = record

        # TODO: history for IP address changes isn't accumulated yet (see get_stored_metadata()).
        prior = None
        for record in ipv4_addresses.values():
            for field in fields:
                if field['field_name'] in record and prior and field['field_name'] in prior and \
                   prior[field['field_name']] != record[field['field_name']]:
                    endpoint.update_property_history(field['entry_type'], field['field_name'], endpoint.endpoint_data.ipv4_addresses['field_name'],
                            prior[field['field_name']], record[field['field_name']])  # pytype: disable=unsupported-operands
                prior = record

        prior = None
        for record in ipv6_addresses.values():
            for field in fields:
                if field['field_name'] in record and prior and field['field_name'] in prior and \
                   prior[field['field_name']] != record[field['field_name']]:
                    endpoint.update_property_history(field['entry_type'], field['field_name'], endpoint.endpoint_data.ipv6_addresses['field_name'],
                            prior[field['field_name']], record[field['field_name']])  # pytype: disable=unsupported-operands
                prior = record

    def store_endpoints(self, endpoints):
        ''' store current endpoints in Redis. '''
        if self.r:
            try:
                serialized_endpoints = []
                for endpoint in endpoints.values():
                    # set metadata
                    mac_addresses, ipv4_addresses, ipv6_addresses = self.get_stored_metadata(
                        str(endpoint.name))
                    self.update_history(
                        endpoint, mac_addresses, ipv4_addresses, ipv6_addresses)
                    endpoint.metadata = {
                        'mac_addresses': mac_addresses,
                        'ipv4_addresses': ipv4_addresses,
                        'ipv6_addresses': ipv6_addresses}
                    redis_endpoint_data = {
                        'name': endpoint.name,
                        'state': endpoint.state,
                        'ignore': endpoint.ignore,
                        'endpoint_data': endpoint.endpoint_data,
                        'next_state': endpoint.p_next_state,
                        'prev_states': endpoint.p_prev_states,
                        'acl_data': endpoint.acl_data,
                        'metadata': endpoint.metadata,
                    }
                    self.hmset(endpoint.name, redis_endpoint_data)
                    mac = endpoint.endpoint_data['mac']
                    self.hmset(mac, {'poseidon_hash': endpoint.name})
                    if not self.r.sismember('mac_addresses', mac):
                        self.r.sadd('mac_addresses', mac)
                    for ip_field in MACHINE_IP_FIELDS:
                        try:
                            machine_ip = ipaddress.ip_address(
                                endpoint.endpoint_data.get(ip_field, None))
                        except ValueError:
                            machine_ip = None
                        if machine_ip:
                            self.hmset(str(machine_ip), {'poseidon_hash': endpoint.name})
                            if not self.r.sismember('ip_addresses', str(machine_ip)):
                                self.r.sadd('ip_addresses', str(machine_ip))
                    serialized_endpoints.append(endpoint.encode())
                self.r.set('p_endpoints', str(serialized_endpoints))
            except Exception as e:  # pragma: no cover
                self.logger.error(
                        'Unable to store endpoints in Redis because {0}'.format(str(e)))

    def inc_network_tools_counts(self):
        if self.r is not None:
            try:
                self.r.hincrby('network_tools_counts', 'ncapture')
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'Failed to update count of plugins because: {0}'.format(str(e)))
