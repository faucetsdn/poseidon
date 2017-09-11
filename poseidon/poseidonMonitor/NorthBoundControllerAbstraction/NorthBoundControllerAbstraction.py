#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
Created on 17 May 2016
@author: dgrossman
'''
import hashlib
import json
import logging
import Queue
import threading
import time
import types
from functools import partial
from os import getenv

from poseidon.baseClasses.Rabbit_Base import Rabbit_Base
from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import BcfProxy
# import ast
# import requests

# logging.basicConfig()
module_logger = logging.getLogger(__name__)


def callback(ch, method, properties, body, q=None):
    module_logger.debug(
        ''' callback, places rabbit data into internal queue'''
        'got a message:{0} {1}'.format(method.routing_key, body))
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        module_logger.error(
            'NorthBoundControllerAbstraction workQueue is None')


class NorthBoundControllerAbstraction(Monitor_Action_Base):
    ''' handle abstracting poseidon from the controllers '''

    def __init__(self):
        super(NorthBoundControllerAbstraction, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name


class Handle_Resource(Monitor_Helper_Base):

    def __init__(self):
        super(Handle_Resource, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__

    def on_get(self, req, resp, resource):
        ''' handle reading endpoint '''
        resp.content_type = 'text/text'
        try:
            resp.body = self.mod_name + ' found: {0}'.format(resource)
        except BaseException:  # pragma: no cover
            pass


class Handle_Periodic(Monitor_Helper_Base):
    ''' handle periodic process, determine if switch state updated '''

    def __init__(self):
        super(Handle_Periodic, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__
        self.retval = {}
        self.times = 0
        self.owner = None
        self.controller = {}
        self.controller['URI'] = None
        self.controller['USER'] = None
        self.controller['PASS'] = None
        self.bcf = None
        self.first_time = True
        self.prev_endpoints = {}
        self.new_endpoints = {}
        self.mirroring = {}
        self.shutdown = {}
        self.do_rabbit = True
        self.m_queue = Queue.Queue()
        self.rabbit_connection_local = None
        self.rabbit_channel_local = None

        if getenv('SKIPRABBIT') is None:
            module_logger.critical('handle_periodic skipping rabbit')
            self.do_rabbit = False
        else:
            module_logger.critical('handle_periodic starting rabbit')
            self.start_rabbit()

        # TODO init the rabbitmq

    # rabbit
    def start_rabbit(self):
        ''' start the rabbit negotiations using the Rabbit base class'''
        # self.init_rabbit()
        rabbit = Rabbit_Base()
        host = 'poseidon-rabbit'
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_NBCA'
        binding_key = ['poseidon.action.#']
        retval = rabbit.make_rabbit_connection(host, exchange, queue_name,
                                               binding_key, total_sleep=30)
        self.rabbit_channel_local = retval[0]
        self.rabbit_connection_local = retval[1]
        self.do_rabbit = retval[2]

        if self.do_rabbit:
            rabbit.start_channel(self.rabbit_channel_local,
                                 callback, 'poseidon_NBCA', self.m_queue)

    def first_run(self):
        ''' do some pre-run setup/configuration '''
        if self.configured:
            self.controller['URI'] = str(
                self.mod_configuration['controller_uri'])
            self.controller['USER'] = str(
                self.mod_configuration['controller_user'])
            self.controller['PASS'] = str(
                self.mod_configuration['controller_pass'])

            myauth = {}
            myauth['password'] = self.controller['PASS']
            myauth['user'] = self.controller['USER']
            try:
                self.bcf = BcfProxy(self.controller['URI'], auth=myauth)
            except BaseException:
                self.logger.error(
                    'BcfProxy coult not connect to {0}'.format(
                        self.controller['URI']))
        else:
            pass

    @staticmethod
    def make_hash(item):
        ''' hash the metadata in a sane way'''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        # GROSSMAN dont nodchp -> dhcp withname makes different hashes
        #{u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': None, u'ip-address': u'10.179.0.100'}}^
        #{u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': u'demo-laptop', u'ip-address': u'10.179.0.100'}}
        # ^^^ make different hashes if name is included

        # for word in ['tenant', 'mac', 'segment', 'name', 'ip-address']:
        for word in ['tenant', 'mac', 'segment', 'ip-address']:
            pre_h = pre_h + str(item.get(str(word), 'missing'))
        h.update(pre_h)
        post_h = h.hexdigest()
        return post_h

    def handle_item(self, item):
        ''' perform an action based on rabbit item'''
        self.logger.debug('handle_item: {0}:{1}'.format(item, type(item)))
        itype = item[0]
        ivalue = item[1]
        ivalue = json.loads(ivalue)
        self.logger.debug(
            'handle_item: ivalue json: {0}:{1}'.format(ivalue, type(ivalue)))

        if itype == 'poseidon.action.start_monitor':
            for my_hash, my_dict in ivalue.iteritems():
                if my_hash in self.new_endpoints:
                    v = self.new_endpoints.pop(my_hash)
                    self.logger.debug(
                        'removed {0} from new_endpoints'.format(v))
                else:
                    self.logger.debug('could not find {0} in {1}'.format(
                        my_hash, self.new_endpoints))

                self.logger.debug(
                    'mirroring :{0}'.format(my_dict['ip-address']))
                self.logger.debug(
                    'mirroring[{0}]={1}'.format(my_hash, my_dict))
                self.bcf.mirror_ip(my_dict['ip-address'])
                self.mirroring[my_hash] = my_dict

        if itype == 'poseidon.action.endpoint_shutdown':
            self.logger.debug(
                'endpoint_shutdown:{0}:{1}'.format(ivalue, type(ivalue)))
            for my_hash, my_dict in ivalue.iteritems():
                bad_ip = my_dict.get('ip-address')
                if bad_ip is not None:
                    self.logger.debug(
                        '****** shutdown {0}:{1}'.format(bad_ip, ivalue))
                    self.bcf.shutdown_ip(bad_ip)
                    self.shutdown[my_hash] = my_dict

        if itype == 'poseidon.action.stop_monitor':
            self.logger.debug('stop_monitor:{0}:{1}'.format(itype, ivalue))
            for my_hash, my_dict in ivalue.iteritems():
                self.logger.debug('stop_monitor_dict:{0}'.format(my_dict))
                my_ip = my_dict.get('ip-address')
                if my_ip is not None:
                    self.logger.debug('***** shutting down {0}'.format(my_ip))
                    self.bcf.unmirror_ip(my_ip)
                    if my_hash in self.mirroring:
                        self.mirroring.pop(my_hash)

    def get_rabbit_work(self):
        '''get work item from queue if exists'''
        # type , value
        workfound = False
        item = None
        self.logger.debug('about to look for work')
        try:
            item = self.m_queue.get(False)
            self.logger.debug('item:{0}'.format(item))
            self.logger.debug('work found')
            workfound = True
        except Queue.Empty:
            pass
        self.logger.debug('done looking for work!')

        if workfound:
            self.handle_item(item)

        return item

    def find_new_machines(self, machines):
        '''parse switch structure to find new machines added to network
        since last call'''
        if self.first_time:
            self.first_time = False
            # TODO db call to see if really need to run things
            for machine in machines:
                h = self.make_hash(machine)
                module_logger.critical(
                    'adding address to known systems {0}'.format(machine))
                self.prev_endpoints[h] = machine
        else:
            for machine in machines:
                h = self.make_hash(machine)
                if h not in self.prev_endpoints and h not in self.mirroring:
                    module_logger.critical(
                        '***** detected new address {0}'.format(machine))
                    self.new_endpoints[h] = machine

    def print_state(self):
        self.logger.debug('*************KNOWN*****************')
        for my_hash, my_dict in self.prev_endpoints.iteritems():
            self.logger.debug('P:{0}:{1}'.format(my_hash, my_dict))
        if len(self.prev_endpoints) == 0:
            self.logger.debug('None')
        self.logger.debug('************UNKNOWN****************')
        for my_hash, my_dict in self.new_endpoints.iteritems():
            self.logger.debug('N:{0}:{1}'.format(my_hash, my_dict))
        if len(self.new_endpoints) == 0:
            self.logger.debug('None')
        self.logger.debug('***********MIRRORING***************')
        for my_hash, my_dict in self.mirroring.iteritems():
            self.logger.debug('M:{0}:{1}'.format(my_hash, my_dict))
        if len(self.mirroring) == 0:
            self.logger.debug('None')
        self.logger.debug('***********SHUTDOWN****************')
        for my_hash, my_dict in self.shutdown.iteritems():
            self.logger.debug('M:{0}:{1}'.format(my_hash, my_dict))
        if len(self.shutdown) == 0:
            self.logger.debug('None')

    def send_new_machines(self):
        '''send listing of new machines to main for decisions'''
        for hashed, machine in self.new_endpoints.iteritems():
            # TODO write findings to main
            r_exchange = 'topic-poseidon-internal'
            r_key = 'poseidon.action.new_machine'
            r_msg = json.dumps({hashed: machine})
            self.rabbit_channel_local.basic_publish(exchange=r_exchange,
                                                    routing_key=r_key,
                                                    body=r_msg)

    def on_get(self, req, resp):
        '''Handles Get requests'''
        self.retval['service'] = self.owner.mod_name + ':' + self.mod_name
        self.retval['times'] = self.times
        self.retval['machines'] = None
        self.retval['resp'] = 'bad'

        current = None
        parsed = None
        machines = {}

        try:
            current = self.bcf.get_endpoints()
            parsed = self.bcf.format_endpoints(current)
            machines = parsed
        except BaseException:
            self.logger.error(
                'Could not establish connection to {0}.'.format(
                    self.controller['URI']))
            self.retval['controller'] = 'Could not establish connection to {0}.'.format(
                self.controller['URI'])

        self.get_rabbit_work()
        self.logger.debug('MACHINES:{0}'.format(machines))
        self.find_new_machines(machines)
        self.send_new_machines()

        self.print_state()

        self.retval['machines'] = parsed
        self.retval['resp'] = 'ok'
        # TODO change response to something reflecting success of traversal
        self.times = self.times + 1
        resp.body = json.dumps(self.retval)


controller_interface = NorthBoundControllerAbstraction()
controller_interface.add_endpoint('Handle_Periodic', Handle_Periodic)
controller_interface.add_endpoint('Handle_Resource', Handle_Resource)
