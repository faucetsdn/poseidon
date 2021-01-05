#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import queue
import random
import sys
import time

import requests

requests.packages.urllib3.disable_warnings()


class Monitor:

    def __init__(self, logger, config, schedule, job_queue, sdnc, prom):
        self.logger = logger
        self.rabbits = []
        self.config = config
        self.job_queue = job_queue
        self.sdnc = sdnc
        self.prom = prom

        # timer class to call things periodically in own thread
        schedule.every(self.config['scan_frequency']).seconds.do(
            self.schedule_job_update_metrics)
        schedule.every(self.config['reinvestigation_frequency']).seconds.do(
            self.schedule_job_reinvestigation_timeout)

    def get_hosts(self):
        # TODO consolidate with update_endpoint_metadata
        hosts = []
        for hash_id, endpoint in self.sdnc.endpoints.items():
            roles, _, _ = endpoint.get_roles_confidences_pcap_labels()
            role = roles[0]
            ipv4_os = endpoint.get_ipv4_os()
            host = {
                'mac': endpoint.endpoint_data['mac'],
                'id': hash_id,
                'role': role,
                'ipv4_os': ipv4_os,
                'state': endpoint.state,
                'tenant': endpoint.endpoint_data['tenant'],
                'port': endpoint.endpoint_data['port'],
                'segment': endpoint.endpoint_data['segment'],
                'ipv4': endpoint.endpoint_data['ipv4']}
            hosts.append(host)
        return hosts

    def job_update_metrics(self):
        self.logger.debug('updating metrics')
        try:
            hosts = self.get_hosts()
            self.prom.update_metrics(hosts)
        except (requests.exceptions.ConnectionError, Exception) as e:  # pragma: no cover
            self.logger.error(
                'Unable to get current state and send it to Prometheus because: {0}'.format(str(e)))
        return 0

    def job_recoprocess(self):
        if not self.sdnc.sdnc:
            for endpoint in self.sdnc.not_copro_ignored_endpoints():
                if endpoint.copro_state != 'copro_nominal':
                    endpoint.copro_nominal()  # pytype: disable=attribute-error
            return 0
        events = 0
        for endpoint in self.sdnc.not_copro_ignored_endpoints('copro_coprocessing'):
            if endpoint.copro_state_timeout(2*self.config['coprocessing_frequency']):
                self.logger.debug(
                    'timing out: {0} and setting to unknown'.format(endpoint.name))
                self.sdnc.uncoprocess_endpoint(endpoint)
                endpoint.copro_unknown()  # pytype: disable=attribute-error
                events += 1
        return events

    def job_reinvestigation_timeout(self):
        ''' put endpoints into the reinvestigation state if possible, and timeout investigations '''
        if not self.sdnc.sdnc:
            for endpoint in self.sdnc.not_ignored_endpoints():
                if endpoint.state != 'known':
                    endpoint.known()  # pytype: disable=attribute-error
            return 0
        events = 0
        timeout = 2*self.config['reinvestigation_frequency']
        for endpoint in self.sdnc.not_ignored_endpoints():
            if endpoint.observed_timeout(timeout):
                self.logger.info(
                    'observation timing out: {0}'.format(endpoint.name))
                endpoint.force_unknown()
                events += 1
            elif endpoint.operation_active() and endpoint.state_timeout(timeout):
                self.logger.info(
                    'mirror timing out: {0}'.format(endpoint.name))
                self.sdnc.unmirror_endpoint(endpoint)
                events += 1
        budget = self.sdnc.investigation_budget()
        candidates = self.sdnc.not_ignored_endpoints('queued')
        if not candidates:
            candidates = self.sdnc.not_ignored_endpoints('known')
        return events + self._schedule_queued_work(
            candidates, budget, 'operate', self.sdnc.mirror_endpoint, shuffle=True)

    def schedule_job_update_metrics(self):
        self.job_queue.put(self.job_update_metrics)

    def schedule_job_reinvestigation_timeout(self):
        self.job_queue.put(self.job_reinvestigation_timeout)

    def _schedule_queued_work(self, queued_endpoints, budget, endpoint_state, endpoint_work, shuffle=False):
        events = 0
        if self.sdnc.sdnc:
            if shuffle:
                random.shuffle(queued_endpoints)
            for endpoint in queued_endpoints[:budget]:
                getattr(endpoint, endpoint_state)()
                endpoint_work(endpoint)
                if endpoint_state in ['trigger_next', 'operate']:
                    # TODO this may not be necessarily true going forward
                    self.prom.prom_metrics['ncapture_count'].inc()
                events += 1
        return events

    # TODO make generic
    def schedule_mirroring(self):
        for endpoint in self.sdnc.not_ignored_endpoints('unknown'):
            endpoint.queue_next('operate')
        budget = self.sdnc.investigation_budget()
        queued_endpoints = [
            endpoint for endpoint in self.sdnc.not_ignored_endpoints('queued')
            if endpoint.operation_requested()]
        queued_endpoints = sorted(queued_endpoints, key=lambda x: x.state_time)
        self.logger.debug('operations {0}, budget {1}, queued {2}'.format(
            str(self.sdnc.investigations), str(budget), str(len(queued_endpoints))))
        return self._schedule_queued_work(queued_endpoints, budget, 'trigger_next', self.sdnc.mirror_endpoint)

    # TODO make generic
    def schedule_coprocessing(self):
        for endpoint in self.sdnc.not_copro_ignored_endpoints('copro_unknown'):
            endpoint.copro_queue_next('copro_coprocess')
        budget = self.sdnc.coprocessing_budget()
        queued_endpoints = self.sdnc.not_copro_ignored_endpoints(
            'copro_queued')
        queued_endpoints = sorted(
            queued_endpoints, key=lambda x: x.copro_state_time)
        self.logger.debug('coprocessing {0}, budget {1}, queued {2}'.format(
            str(self.sdnc.coprocessing), str(budget), str(len(queued_endpoints))))
        return self._schedule_queued_work(queued_endpoints, budget, 'copro_trigger_next', self.sdnc.coprocess_endpoint)
