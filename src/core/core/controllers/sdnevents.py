import json
import queue
import time
from collections import defaultdict
from functools import partial

from poseidon_core.helpers.actions import Actions
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.rabbit import Rabbit


class SDNEvents:

    def __init__(self, logger, prom, sdnc):
        self.logger = logger
        self.prom = prom
        self.m_queue = queue.Queue()
        self.job_queue = queue.Queue()
        self.rabbits = []
        self.config = Config().get_config()
        self.sdnc = sdnc
        self.sdnc.default_endpoints()
        self.prom.update_endpoint_metadata(self.sdnc.endpoints)

    def create_message_queue(self, host, port, exchange, binding_key):
        waiting = True
        while waiting:
            rabbit = Rabbit()
            rabbit.make_rabbit_connection(
                host, port, exchange, binding_key)
            rabbit.start_channel(
                self.rabbit_callback, self.m_queue)
            waiting = False
        self.rabbits.append(rabbit)

    def start_message_queues(self):
        host = self.config['FA_RABBIT_HOST']
        port = int(self.config['FA_RABBIT_PORT'])
        exchange = 'topic-poseidon-internal'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        self.create_message_queue(
            host, port, exchange, binding_key)
        exchange = self.config['FA_RABBIT_EXCHANGE']
        binding_key = [self.config['FA_RABBIT_ROUTING_KEY']+'.#']
        self.create_message_queue(
            host, port, exchange, binding_key)

    def merge_metadata(self, new_metadata):
        updated = set()
        metadata_types = {
            'mac_addresses': self.sdnc.endpoints_by_mac,
            'ipv4_addresses': self.sdnc.endpoints_by_ip,
            'ipv6_addresses': self.sdnc.endpoints_by_ip,
        }
        for metadata_type, metadata_lookup in metadata_types.items():
            type_new_metadata = new_metadata.get(metadata_type, {})
            for key, data in type_new_metadata.items():
                endpoints = metadata_lookup(key)
                if endpoints:
                    endpoint = endpoints[0]
                    if metadata_type not in endpoint.metadata:
                        endpoint.metadata[metadata_type] = defaultdict(dict)
                    endpoint.metadata[metadata_type][key].update(data)
                    updated.add(endpoint)
        return updated

    def format_rabbit_message(self, item, faucet_event, remove_list):
        '''
        read a message off the rabbit_q
        the message should be item = (routing_key,msg)
        '''
        routing_key, my_obj = item
        self.logger.debug(
            'routing_key: {0} rabbit_message: {1}'.format(routing_key, my_obj))

        def handler_algos_decider(my_obj):
            self.logger.debug('decider value:{0}'.format(my_obj))
            data = my_obj.get('data', None)
            results = my_obj.get('results', {})
            tool = results.get('tool', None)
            if isinstance(data, dict) and data:
                new_metadata = data
                if tool == 'p0f':
                    ip_metadata = {}
                    for ip, ip_data in data.items():
                        if ip_data and ip_data.get('full_os', None):
                            ip_metadata[ip] = ip_data
                    new_metadata = {'ipv4_addresses': ip_metadata}
                elif tool == 'networkml':
                    mac_metadata = {}
                    for name, message in data.items():
                        if name == 'pcap':
                            continue
                        if message.get('valid', False):
                            source_mac = message.get('source_mac', None)
                            if source_mac:
                                mac_metadata[source_mac] = message
                    new_metadata = {'mac_addresses': mac_metadata}
                # Generic handler for future tools.
                updated = self.merge_metadata(new_metadata)
                if updated:
                    for endpoint in updated:
                        if endpoint.operation_active():
                            self.sdnc.unmirror_endpoint(endpoint)
                    return data
            return {}

        def handler_action_ignore(my_obj):
            for name in my_obj:
                endpoint = self.sdnc.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = True
            return {}

        def handler_action_clear_ignored(my_obj):
            for name in my_obj:
                endpoint = self.sdnc.endpoints.get(name, None)
                if endpoint:
                    endpoint.ignore = False
            return {}

        def handler_action_change(my_obj):
            for name, state in my_obj:
                endpoint = self.sdnc.endpoints.get(name, None)
                if endpoint:
                    try:
                        if endpoint.operation_active():
                            self.sdnc.unmirror_endpoint(endpoint)
                        # pytype: disable=attribute-error
                        endpoint.machine_trigger(state)
                        endpoint.p_next_state = None
                        if endpoint.operation_active():
                            self.sdnc.mirror_endpoint(endpoint)
                            self.prom.prom_metrics['ncapture_count'].inc()
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to change endpoint {0} because: {1}'.format(endpoint.name, str(e)))
            return {}

        def handler_action_update_acls(my_obj):
            for ip in my_obj:
                rules = my_obj[ip]
                endpoints = self.sdnc.endpoints_by_ip(ip)
                if endpoints:
                    endpoint = endpoints[0]
                    try:
                        status = Actions(
                            endpoint, self.sdnc.sdnc).update_acls(
                                rules_file=self.config['RULES_FILE'], endpoints=endpoints, force_apply_rules=rules)
                        if not status:
                            self.logger.warning(
                                'Unable to apply rules: {0} to endpoint: {1}'.format(rules, endpoint.name))
                    except Exception as e:
                        self.logger.error(
                            'Unable to apply rules: {0} to endpoint: {1} because {2}'.format(rules, endpoint.name, str(e)))
            return {}

        def handler_action_remove(my_obj):
            remove_list.extend([name for name in my_obj])
            return {}

        def handler_action_remove_ignored(_my_obj):
            remove_list.extend([
                endpoint.name for endpoint in self.sdnc.endpoints.values()
                if endpoint.ignore])
            return {}

        def handler_faucet_event(my_obj):
            if self.sdnc and self.sdnc.sdnc:
                faucet_event.append(my_obj)
                return my_obj
            return {}

        handlers = {
            'poseidon.algos.decider': handler_algos_decider,
            'poseidon.action.ignore': handler_action_ignore,
            'poseidon.action.clear.ignored': handler_action_clear_ignored,
            'poseidon.action.change': handler_action_change,
            'poseidon.action.update_acls': handler_action_update_acls,
            'poseidon.action.remove': handler_action_remove,
            'poseidon.action.remove.ignored': handler_action_remove_ignored,
            self.config['FA_RABBIT_ROUTING_KEY']: handler_faucet_event,
        }

        handler = handlers.get(routing_key, None)
        if handler is not None:
            ret_val = handler(my_obj)
            return ret_val, True

        self.logger.error(
            'no handler for routing_key {0}'.format(routing_key))
        return {}, False

    def update_routing_key_time(self, routing_key):
        if self.prom:
            self.prom.prom_metrics['last_rabbitmq_routing_key_time'].labels(
                routing_key=routing_key).set(time.time())

    def handle_rabbit(self):
        events = 0
        faucet_event = []
        remove_list = []
        while True:
            found_work, rabbit_msg = self.prom.runtime_callable(
                partial(self.get_q_item, self.m_queue))
            if not found_work:
                break
            events += 1
            # faucet_event and remove_list get updated as references because partial()
            self.prom.runtime_callable(
                partial(self.format_rabbit_message, rabbit_msg, faucet_event, remove_list))
        return (events, faucet_event, remove_list)

    def ignore_rabbit(self, routing_key, body):
        ''' drop ignored messages. '''
        if routing_key == self.config['FA_RABBIT_ROUTING_KEY']:
            if self.sdnc and self.sdnc.sdnc:
                if self.sdnc.sdnc.ignore_event(body):
                    return True
        return False

    def rabbit_callback(self, ch, method, _properties, body, q=None):
        ''' callback, places rabbit data into internal queue'''
        body = json.loads(body)
        self.logger.debug('got a message: {0}:{1} (qsize {2})'.format(
            method.routing_key, body, q.qsize()))
        if q is not None:
            self.update_routing_key_time(method.routing_key)
            if not self.ignore_rabbit(method.routing_key, body):
                q.put((method.routing_key, body))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def process(self, monitor):
        while True:
            events, faucet_event, remove_list = self.prom.runtime_callable(
                self.handle_rabbit)
            if remove_list:
                for endpoint_name in remove_list:
                    if endpoint_name in self.sdnc.endpoints:
                        del self.sdnc.endpoints[endpoint_name]
            if faucet_event:
                self.prom.runtime_callable(
                    partial(self.sdnc.check_endpoints, faucet_event))
            # schedule_mirroring should be abstracted out
            events += self.prom.runtime_callable(monitor.schedule_mirroring)
            found_work, schedule_func = self.prom.runtime_callable(
                partial(self.get_q_item, self.job_queue))
            if found_work and callable(schedule_func):
                events += self.prom.runtime_callable(schedule_func)
            if events:
                self.prom.update_endpoint_metadata(self.sdnc.endpoints)
            time.sleep(1)

    @staticmethod
    def get_q_item(q):
        '''
        attempt to get a work item from the queue
        m_queue -> (routing_key, body)
        a read from get_q_item should be of the form
        (boolean,(routing_key, body))
        '''
        try:
            item = q.get_nowait()
            q.task_done()
            return (True, item)
        except queue.Empty:  # pragma: no cover
            pass

        return (False, None)
