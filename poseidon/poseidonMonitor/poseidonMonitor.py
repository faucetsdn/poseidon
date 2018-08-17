#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This example is a test of a usable API demonstrating the test and documentation
workflow for the code base.

Created on 17 May 2016
@author: Charlie Lewis, dgrossman
"""
import ast
import json
import random
import signal
import socket
import sys
import threading
import time
from binascii import hexlify
from functools import partial
from os import getenv

import queue as Queue
import requests
import schedule
from prometheus_client import Gauge
from prometheus_client import start_http_server

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Rabbit_Base import Rabbit_Base
from poseidon.poseidonMonitor.Config.Config import config_interface
from poseidon.poseidonMonitor.endPoint import EndPoint
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import \
    controller_interface
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import \
    BcfProxy

requests.packages.urllib3.disable_warnings()

CTRL_C = dict()
CTRL_C['STOP'] = False


def schedule_job_kickurl(func, logger):
    ''' periodically ask the controller for its state '''

    def ip2int(ip):
        ''' convert ip quad octet string to an int '''
        if ip in [None, '::']:
            res = 0
        elif ':' in ip:
            res = int(hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)
        else:
            o = list(map(int, ip.split('.')))
            res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
        return res

    func.NorthBoundControllerAbstraction.get_endpoint(
        'Update_Switch_State').update_endpoint_state(messages=func.faucet_event)
    # check the length didn't change before wiping it out
    func.faucet_event = []

    # get current state
    r = requests.get('http://poseidon-api:8000/v1/network_full')

    # send results to prometheus
    hosts = r.json()['dataset']
    metrics = {'roles': {},
               'oses': {},
               'current_states': {('Poseidon', 'KNOWN'): 0,
                                  ('Poseidon', 'UNKNOWN'): 0,
                                  ('Poseidon', 'MIRRORING'): 0,
                                  ('Poseidon', 'SHUTDOWN'): 0,
                                  ('Poseidon', 'REINVESTIGATING'): 0},
               'vlans': {},
               'record_sources': {},
               'port_tenants': {},
               'port_hosts': {},
               'inactives': 0,
               'actives': 0}
    for host in hosts:
        if host['active'] == 0:
            metrics['inactives'] += 1
        if host['active'] == 1:
            metrics['actives'] += 1
        if (host['record_source'], host['role']) in metrics['roles']:
            if host['active'] == 1:
                metrics['roles'][(host['record_source'], host['role'])] += 1
        else:
            if host['active'] == 1:
                metrics['roles'][(host['record_source'], host['role'])] = 1
            else:
                metrics['roles'][(host['record_source'], host['role'])] = 0

        if (host['record_source'], host['os']) in metrics['oses']:
            if host['active'] == 1:
                metrics['oses'][(host['record_source'], host['os'])] += 1
        else:
            if host['active'] == 1:
                metrics['oses'][(host['record_source'], host['os'])] = 1
            else:
                metrics['oses'][(host['record_source'], host['os'])] = 0

        if (host['record_source'], host['state']) in metrics['current_states']:
            if host['active'] == 1:
                metrics['current_states'][(host['record_source'],
                                           host['state'])] += 1
        else:
            if host['active'] == 1:
                metrics['current_states'][(host['record_source'],
                                           host['state'])] = 1
            else:
                metrics['current_states'][(host['record_source'],
                                           host['state'])] = 0

        if (host['record_source'], host['tenant']) in metrics['vlans']:
            if host['active'] == 1:
                metrics['vlans'][(host['record_source'], host['tenant'])] += 1
        else:
            if host['active'] == 1:
                metrics['vlans'][(host['record_source'], host['tenant'])] = 1
            else:
                metrics['vlans'][(host['record_source'], host['tenant'])] = 0

        if (host['record_source']) in metrics['record_sources']:
            if host['active'] == 1:
                metrics['record_sources'][(host['record_source'])] += 1
        else:
            if host['active'] == 1:
                metrics['record_sources'][(host['record_source'])] = 1
            else:
                metrics['record_sources'][(host['record_source'])] = 0

        if (host['port'], host['tenant']) in metrics['port_tenants']:
            if host['active'] == 1:
                metrics['port_tenants'][(host['port'], host['tenant'])] += 1
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
                func.prom_metrics['behavior'].labels(ip=host['ip'],
                                                     mac=host['mac'],
                                                     tenant=host['tenant'],
                                                     segment=host['segment'],
                                                     port=host['port'],
                                                     role=host['role'],
                                                     os=host['os'],
                                                     record_source=host['record_source']).set(host['behavior'])
                func.prom_metrics['ip_table'].labels(mac=host['mac'],
                                                     tenant=host['tenant'],
                                                     segment=host['segment'],
                                                     port=host['port'],
                                                     role=host['role'],
                                                     os=host['os'],
                                                     hash_id=host['hash'],
                                                     record_source=host['record_source']).set(ip2int(host['ip']))
        except Exception as e:  # pragma: no cover
            logger.error(
                'unable to send {0} results to prometheus because {1}'.format(host, str(e)))

    try:
        for role in metrics['roles']:
            func.prom_metrics['roles'].labels(record_source=role[0],
                                              role=role[1]).set(metrics['roles'][role])
        for os_t in metrics['oses']:
            func.prom_metrics['oses'].labels(record_source=os_t[0],
                                             os=os_t[1]).set(metrics['oses'][os_t])
        for current_state in metrics['current_states']:
            func.prom_metrics['current_states'].labels(record_source=current_state[0],
                                                       current_state=current_state[1]).set(metrics['current_states'][current_state])
        for vlan in metrics['vlans']:
            func.prom_metrics['vlans'].labels(record_source=vlan[0],
                                              tenant=vlan[1]).set(metrics['vlans'][vlan])
        for record_source in metrics['record_sources']:
            func.prom_metrics['record_sources'].labels(record_source=record_source).set(
                metrics['record_sources'][record_source])
        for port_tenant in metrics['port_tenants']:
            func.prom_metrics['port_tenants'].labels(port=port_tenant[0],
                                                     tenant=port_tenant[1]).set(metrics['port_tenants'][port_tenant])
        for port_host in metrics['port_hosts']:
            func.prom_metrics['port_hosts'].labels(
                port=port_host).set(metrics['port_hosts'][port_host])
        func.prom_metrics['inactive'].set(metrics['inactives'])
        func.prom_metrics['active'].set(metrics['actives'])
    except Exception as e:  # pragma: no cover
        logger.error(
            'unable to send results to prometheus because {0}'.format(str(e)))


def rabbit_callback(ch, method, properties, body, q=None):
    ''' callback, places rabbit data into internal queue'''
    Logger.poseidon_logger.debug('got a message: {0}:{1}:{2}'.format(
        method.routing_key, body, type(body)))
    # TODO more
    if q is not None:
        q.put((method.routing_key, body))
    else:
        Logger.poseidon_logger.debug('posedionMain workQueue is None')


def schedule_thread_worker(schedule, logger):
    ''' schedule thread, takes care of running processes in the future '''
    global CTRL_C
    logLine = 'starting thread_worker'
    logger.debug(logLine)
    while not CTRL_C['STOP']:
        sys.stdout.flush()
        schedule.run_pending()
        time.sleep(1)
    logger.debug('Threading stop:{0}'.format(
        threading.current_thread().getName()))
    sys.exit()


def schedule_job_reinvestigation(max_investigations, endpoints, logger):
    ''' put endpoints into the reinvestigation state if possible '''
    ostr = 'reinvestigation time'
    logger.debug(ostr)
    logger.debug('endpoints:{0}'.format(endpoints))
    candidates = []

    currently_investigating = 0
    for my_hash, my_value in endpoints.state.items():
        if my_value.state == 'REINVESTIGATING' or my_value.next_state == 'REINVESTIGATING':
            currently_investigating += 1
        elif my_value.state == 'KNOWN':
            candidates.append(my_hash)

    # get random order of things that are known
    random.shuffle(candidates)

    if currently_investigating < max_investigations:
        ostr = 'room to investigate'
        logger.debug(ostr)
        for x in range(max_investigations - currently_investigating):
            if len(candidates) >= 1:
                chosen = candidates.pop()
                ostr = 'starting investigation {0}:{1}'.format(x, chosen)
                logger.debug(ostr)
                endpoints.state[chosen].next_state = 'REINVESTIGATING'
    else:
        ostr = 'investigators all busy'
        logger.debug(ostr)


class Monitor(object):

    def __init__(self, skip_rabbit):
        # get the logger setup
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.mod_configuration = dict()
        Logger.logger_config(None)

        self.mod_name = self.__class__.__name__
        self.skip_rabbit = skip_rabbit

        # prometheus
        self.prom_metrics = {}

        # timer class to call things periodically in own thread
        self.schedule = schedule

        # rabbit
        self.rabbit_channel_local = None
        self.rabbit_chanel_connection_local = None
        self.rabbit_thread = None

        # environment variables
        self.fa_rabbit_enabled = None
        self.fa_rabbit_host = None
        self.fa_rabbit_port = None
        self.fa_rabbit_exchange = None
        self.fa_rabbit_exchange_type = None
        self.fa_rabbit_routing_key = None

        self.actions = dict()
        self.Config = config_interface
        self.Config.set_owner(self)
        self.NorthBoundControllerAbstraction = controller_interface
        self.NorthBoundControllerAbstraction.set_owner(self)

        self.configSelf()

        # set the logger level
        Logger.set_level(self.mod_configuration['logger_level'])

        # check
        self.Config.configure()
        self.Config.first_run()
        self.Config.configure_endpoints()

        self.m_queue = Queue.Queue()
        self.faucet_event = []

        # check
        self.NorthBoundControllerAbstraction.configure()
        self.NorthBoundControllerAbstraction.first_run()
        self.NorthBoundControllerAbstraction.configure_endpoints()

        # make a shortcut
        self.uss = self.NorthBoundControllerAbstraction.get_endpoint(
            'Update_Switch_State')

        # TODO better error checking needed here since this is user input
        scan_frequency = int(self.mod_configuration['scan_frequency'])

        reinvestigation_frequency = int(
            self.mod_configuration['reinvestigation_frequency'])
        max_concurrent_reinvestigations = int(
            self.mod_configuration['max_concurrent_reinvestigations'])

        try:
            self.fa_rabbit_enabled = ast.literal_eval(
                self.mod_configuration['FA_RABBIT_ENABLED'])
            self.fa_rabbit_host = str(
                self.mod_configuration['FA_RABBIT_HOST'])
            self.fa_rabbit_port = int(
                self.mod_configuration['FA_RABBIT_PORT'])
            self.fa_rabbit_exchange = str(
                self.mod_configuration['FA_RABBIT_EXCHANGE'])
            self.fa_rabbit_exchange_type = str(
                self.mod_configuration['FA_RABBIT_EXCHANGE_TYPE'])
            self.fa_rabbit_routing_key = str(
                self.mod_configuration['FA_RABBIT_ROUTING_KEY'])
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Unable to see Faucet Rabbit configuration because: ' + str(e))

        self.schedule.every(scan_frequency).seconds.do(
            partial(schedule_job_kickurl, func=self, logger=self.poseidon_logger))

        self.schedule.every(reinvestigation_frequency).seconds.do(
            partial(schedule_job_reinvestigation,
                    max_investigations=max_concurrent_reinvestigations,
                    endpoints=self.NorthBoundControllerAbstraction.get_endpoint(
                        'Update_Switch_State').endpoints,
                    logger=self.poseidon_logger))

        self.schedule_thread = threading.Thread(
            target=partial(
                schedule_thread_worker,
                schedule=self.schedule,
                logger=self.poseidon_logger),
            name='st_worker')

    def configSelf(self):
        ''' get configuraiton for this module '''
        conf = self.Config.get_endpoint('Handle_SectionConfig')
        for item in conf.direct_get(self.mod_name):
            k, v = item
            self.mod_configuration[k] = v
        ostr = '{0}:config:{1}'.format(self.mod_name, self.mod_configuration)
        self.poseidon_logger.debug(ostr)

    def update_next_state(self, ml_returns):
        ''' generate the next_state from known information '''
        next_state = None
        current_state = None
        endpoints = self.uss.return_endpoint_state()
        for my_hash in endpoints.state:
            endpoint = endpoints.state[my_hash]
            current_state = endpoint.state

            # TODO move this lower with the rest of the checks
            if current_state == 'UNKNOWN':
                if endpoint.next_state != 'KNOWN':
                    endpoint.next_state = 'MIRRORING'

        for my_hash in ml_returns:
            if my_hash in endpoints.state:
                endpoint = endpoints.state[my_hash]
                #
                #    {'4ee39d254db3e4a5264b75ce8ae312d69f9e73a3': {
                #        'classification': {
                #            'confidences': [0.9983864533039954,
                #                            0.0010041873867962805,
                #                            0.00042691313815914093],
                #            'labels': ['Unknown',
                #                      'Smartphone',
                #                      'Developer '
                #                      'workstation']
                #             },
                #            'decisions': {
                #                            'behavior': 'normal',
                #                            'investigate': True
                #             },
                #            'timestamp': 1508366767.45571,
                #            'valid': True
                #        }
                #    }
                #
                # TODO is this the best place for this?
                if ml_returns[my_hash]['valid']:
                    current_state = endpoint.state
                    ml_decision = ml_returns[my_hash]['decisions']['behavior']
                    self.poseidon_logger.debug(
                        'ML_DECISION:{0}'.format(ml_decision))
                    if current_state == 'REINVESTIGATING':
                        if ml_decision == 'normal':
                            self.uss.endpoints.change_endpoint_nextstate(
                                my_hash, 'KNOWN')
                            self.poseidon_logger.debug(
                                'REINVESTIGATION Making KNOWN')
                        else:
                            self.uss.endpoints.change_endpoint_nextstate(
                                my_hash, 'UNKNOWN')
                            self.poseidon_logger.debug(
                                'REINVESTIGATION Making UNKNOWN')
                    if current_state == 'MIRRORING':
                        if ml_decision == 'normal':
                            self.uss.endpoints.change_endpoint_nextstate(
                                my_hash, 'KNOWN')
                            self.poseidon_logger.debug(
                                'MIRRORING Making KNOWN')
                        else:
                            self.uss.endpoints.change_endpoint_nextstate(
                                my_hash, 'SHUTDOWN')
                            self.poseidon_logger.debug(
                                'MIRRORING Making SHUTDOWN')

    def start_vent_collector(self, dev_hash, num_captures=1):
        '''
        Given a device hash and optionally a number of captures
        to be taken, starts vent collector for that device with the
        options specified in poseidon.config.
        '''
        endpoints = self.uss.return_endpoint_state()
        endpoint = endpoints.state.get(dev_hash, EndPoint(None))

        should_start = True
        should_start = (isinstance(self.uss.sdnc, BcfProxy) and self.uss.sdnc.get_span_fabric()) or (
            not isinstance(self.uss.sdnc, BcfProxy))

        payload = {
            'nic': self.mod_configuration['collector_nic'],
            'id': dev_hash,
            'interval': self.mod_configuration['collector_interval'],
            'filter': '\'ether host {0}\''.format(
                self.uss.endpoints.get_endpoint_mac(dev_hash)),
            'iters': str(num_captures),
            'metadata': endpoint.to_str()}

        self.poseidon_logger.debug('vent payload: ' + str(payload))

        vent_addr = self.mod_configuration['vent_ip'] + \
            ':' + self.mod_configuration['vent_port']
        uri = 'http://' + vent_addr + '/create'

        try:
            if should_start:
                resp = requests.post(uri, data=json.dumps(payload))
                self.poseidon_logger.debug('collector response: ' + resp.text)
            else:
                self.poseidon_logger.debug(
                    'collector not started due to invalid span fabric configuration.')

        except Exception as e:  # pragma: no cover
            self.poseidon_logger.debug(
                'failed to start vent collector' + str(e))

    # returns a dictionary of existing collectors keyed on dev_hash
    def get_vent_collectors(self):
        vent_addr = self.mod_configuration['vent_ip'] + \
            ':' + self.mod_configuration['vent_port']
        uri = 'http://' + vent_addr + '/list'
        statuses = None
        try:
            resp = requests.get(uri)
            text = resp.text
            if text.index('True') != -1:
                items = ast.literal_eval(
                    text[text.find(',')+2:text.rfind(')')])
                collectors = {}
                for item in items:
                    host = item['args'][4][5:]
                    coll = Collector(item['id'], item['args'][0], item['args'][1],
                                     item['args'][2], item['args'][3], host, item['status'])
                    collectors.update({coll.hash: coll})
                statuses = collectors

            self.poseidon_logger.debug('collector list response: ' + resp.text)
        except Exception as e:  # pragma: no cover
            statuses = e
            self.poseidon_logger.debug(
                'failed to get vent collector statuses' + str(e))

        return statuses

    def host_has_active_collectors(self, dev_hash):
        active_collectors_exist = False

        collectors = self.get_vent_collectors()

        if dev_hash in collectors:
            hash_coll = collectors[dev_hash]
        else:
            self.logger.warning(
                'Key: {0} not found in collector dictionary. '
                'Treating this as the existence of multiple active'
                'collectors'.format(dev_hash)
            )
            return True

        for c in collectors:
            self.poseidon_logger.debug(c)
            if (
                collectors[c].hash != dev_hash and
                collectors[c].host == hash_coll.host and
                collectors[c].status != 'exited'
            ):
                active_collectors_exist = True
                break

        return active_collectors_exist

    def format_rabbit_message(self, item):
        ''' read a message off the rabbit_q
        the message should be item = (routing_key,msg)
        '''
        ret_val = {}

        routing_key, my_obj = item
        self.poseidon_logger.debug('rabbit_message:{0}'.format(my_obj))
        # my_obj: (hash,data)
        my_obj = json.loads(my_obj)
        self.poseidon_logger.debug('routing_key:{0}'.format(routing_key))
        if routing_key == 'poseidon.algos.decider':
            self.poseidon_logger.debug('decider value:{0}'.format(my_obj))
            # if valid response then send along otherwise nothing
            for key in my_obj:
                ret_val[key] = my_obj[key]
        elif routing_key == self.fa_rabbit_routing_key:
            self.poseidon_logger.debug('FAUCET Event:{0}'.format(my_obj))
            for key in my_obj:
                ret_val[key] = my_obj[key]
        # TODO do something with recomendation
        return ret_val

    def process(self):
        '''
        processing event loop
        {
        while should not be shutdown
        get data from rabbit
        calculate endpoint next_state
        effect changes to endpoints to make state=next_state
        }
        '''

        global CTRL_C
        signal.signal(signal.SIGINT, partial(self.signal_handler))
        while not CTRL_C['STOP']:
            try:
                time.sleep(1)
                found_work, item = self.get_q_item()
                ml_returns = {}

                # plan out the transitions
                if found_work and item[0] != self.fa_rabbit_routing_key:
                    # TODO make this read until nothing in q
                    ml_returns = self.format_rabbit_message(item)
                    self.poseidon_logger.debug('\n\n\n**********************')
                    self.poseidon_logger.debug(
                        'ml_returns:{0}'.format(ml_returns))
                    self.poseidon_logger.debug('**********************\n\n\n')
                elif found_work and item[0] == self.fa_rabbit_routing_key:
                    self.faucet_event.append(self.format_rabbit_message(item))
                    self.poseidon_logger.debug('\n\n\n**********************')
                    self.poseidon_logger.debug(
                        'faucet_event:{0}'.format(self.faucet_event))
                    self.poseidon_logger.debug('**********************\n\n\n')

                eps = self.uss.endpoints
                state_transitions = self.update_next_state(ml_returns)

                # make the transitions
                for endpoint_hash in eps.state:
                    current_state = eps.get_endpoint_state(endpoint_hash)
                    next_state = eps.get_endpoint_next(endpoint_hash)

                    # dont do anything
                    if next_state == 'NONE':
                        continue

                    eps.print_endpoint_state()

                    if next_state == 'MIRRORING':
                        self.poseidon_logger.debug(
                            'updating:{0}:{1}->{2}'.format(endpoint_hash,
                                                           current_state,
                                                           next_state))
                        self.poseidon_logger.debug(
                            '*********** U NOTIFY VENT ***********')
                        self.start_vent_collector(endpoint_hash)
                        self.poseidon_logger.debug(
                            '*********** U MIRROR PORT ***********')
                        self.uss.mirror_endpoint(
                            endpoint_hash, messages=self.faucet_event)
                    if next_state == 'REINVESTIGATING':
                        self.poseidon_logger.debug(
                            'updating:{0}:{1}->{2}'.format(endpoint_hash,
                                                           current_state,
                                                           next_state))
                        self.poseidon_logger.debug(
                            '*********** R NOTIFY VENT ***********')
                        self.start_vent_collector(endpoint_hash)
                        self.poseidon_logger.debug(
                            '*********** R MIRROR PORT ***********')
                        self.uss.mirror_endpoint(
                            endpoint_hash, messages=self.faucet_event)
                    if next_state == 'KNOWN':
                        if (current_state == 'REINVESTIGATING' or
                                current_state == 'MIRRORING'):
                            if not self.host_has_active_collectors(endpoint_hash):
                                self.poseidon_logger.debug(
                                    '*********** ' +
                                    current_state[0] +
                                    ' UN-MIRROR PORT ***********')
                                self.uss.unmirror_endpoint(
                                    endpoint_hash, messages=self.faucet_event)
                            else:
                                self.poseidon_logger.debug(
                                    '*********** ' +
                                    current_state[0] +
                                    ' CAN NOT UN-MIRROR PORT BECAUSE OF ACTIVE COLLECTOR ***********')
                            eps.change_endpoint_state(endpoint_hash)
                        if current_state == 'UNKNOWN':
                            if not self.host_has_active_collectors(endpoint_hash):
                                self.poseidon_logger.debug(
                                    '*********** U UN-MIRROR PORT ***********')
                                self.uss.unmirror_endpoint(
                                    endpoint_hash, messages=self.faucet_event)
                            else:
                                self.poseidon_logger.debug(
                                    '*********** U UN-MIRROR PORT ***********')
                            eps.change_endpoint_state(endpoint_hash)
                    if next_state == 'SHUTDOWN':
                        self.poseidon_logger.debug(
                            'updating:{0}:{1}->{2}'.format(endpoint_hash,
                                                           current_state,
                                                           next_state))
                        self.uss.shutdown_endpoint(endpoint_hash)

                    eps.print_endpoint_state()
            except Exception as e:  # pragma: no cover
                self.poseidon_logger.debug(
                    'iteration failed because: {0}'.format(str(e)))

    def get_q_item(self):
        ''' attempt to get a workitem from the queue'''
        ''' m_queue -> (routing_key, body)
            a read from get_q_item should be of the form
            (boolean,(routing_key, body))

        '''
        found_work = False
        item = None
        global CTRL_C

        if not CTRL_C['STOP']:
            try:
                item = self.m_queue.get(False)
                found_work = True
            except Queue.Empty:  # pragma: no cover
                pass

        return (found_work, item)

    def signal_handler(self, signal, frame):
        ''' hopefully eat a CTRL_C and signal system shutdown '''
        global CTRL_C
        CTRL_C['STOP'] = True
        self.poseidon_logger.debug('=================CTRLC{0}'.format(CTRL_C))
        try:
            for job in self.schedule.jobs:
                self.poseidon_logger.debug('CTRLC:{0}'.format(job))
                self.schedule.cancel_job(job)
            self.rabbit_channel_connection_local.close()
            sys.exit()
        except BaseException:  # pragma: no cover
            pass


class Collector(object):
    def __init__(self, id, nic, interval, hash, iterations, host, status):
        self.id = id
        self.nic = nic
        self.interval = interval
        self.hash = hash
        self.iterations = iterations
        self.host = host
        self.status = status


def main(skip_rabbit=False):  # pragma: no cover
    ''' main function '''
    pmain = Monitor(skip_rabbit=skip_rabbit)

    # declare prometheus variables
    pmain.prom_metrics['inactive'] = Gauge('poseidon_endpoint_inactive',
                                           'Number of endpoints that are inactive')
    pmain.prom_metrics['active'] = Gauge('poseidon_endpoint_active',
                                         'Number of endpoints that are active')
    pmain.prom_metrics['behavior'] = Gauge('poseidon_endpoint_behavior',
                                           'Behavior of an endpoint, 0 is normal, 1 is abnormal',
                                           ['ip',
                                            'mac',
                                            'tenant',
                                            'segment',
                                            'port',
                                            'role',
                                            'os',
                                            'record_source'])
    pmain.prom_metrics['ip_table'] = Gauge('poseidon_endpoint_ip_table',
                                           'IP Table',
                                           ['mac',
                                            'tenant',
                                            'segment',
                                            'port',
                                            'role',
                                            'os',
                                            'hash_id',
                                            'record_source'])
    pmain.prom_metrics['roles'] = Gauge('poseidon_endpoint_roles',
                                        'Number of endpoints by role',
                                        ['record_source',
                                         'role'])
    pmain.prom_metrics['oses'] = Gauge('poseidon_endpoint_oses',
                                       'Number of endpoints by OS',
                                       ['record_source',
                                        'os'])
    pmain.prom_metrics['current_states'] = Gauge('poseidon_endpoint_current_states',
                                                 'Number of endpoints by current state',
                                                 ['record_source',
                                                  'current_state'])
    pmain.prom_metrics['vlans'] = Gauge('poseidon_endpoint_vlans',
                                        'Number of endpoints by VLAN',
                                        ['record_source',
                                         'tenant'])
    pmain.prom_metrics['record_sources'] = Gauge('poseidon_endpoint_record_sources',
                                                 'Number of endpoints by record source',
                                                 ['record_source'])
    pmain.prom_metrics['port_tenants'] = Gauge('poseidon_endpoint_port_tenants',
                                               'Number of tenants by port',
                                               ['port',
                                                'tenant'])
    pmain.prom_metrics['port_hosts'] = Gauge('poseidon_endpoint_port_hosts',
                                             'Number of hosts by port',
                                             ['port'])
    # start prometheus
    start_http_server(9304)

    if not skip_rabbit:
        rabbit = Rabbit_Base()
        host = pmain.mod_configuration['rabbit_server']
        port = int(pmain.mod_configuration['rabbit_port'])
        exchange = 'topic-poseidon-internal'
        queue_name = 'poseidon_main'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    if pmain.fa_rabbit_enabled:
        rabbit = Rabbit_Base()
        host = pmain.fa_rabbit_host
        port = pmain.fa_rabbit_port
        exchange = pmain.fa_rabbit_exchange
        queue_name = 'poseidon_main'
        binding_key = [pmain.fa_rabbit_routing_key+'.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            rabbit_callback,
            queue_name,
            pmain.m_queue)

    pmain.schedule_thread.start()

    # loop here until told not to
    pmain.process()

    pmain.poseidon_logger.debug('SHUTTING DOWN')
    pmain.poseidon_logger.debug('EXITING')
    sys.exit(0)


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
