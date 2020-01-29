# -*- coding: utf-8 -*-
"""
Created on 9 December 2018
@author: Charlie Lewis
"""
import ast
import json
import logging

import requests

from poseidon.helpers.config import Config


class Coprocessor(object):

    def __init__(self, endpoint, switch, iterations=1):
        self.logger = logging.getLogger('coprocessor')
        self.controller = Config().get_config()
        self.endpoint = endpoint
        self.id = endpoint.name
        self.mac = endpoint.endpoint_data['mac']
        nic = self.controller['coprocessor_nic']
        try:
            eval_nic = ast.literal_eval(nic)
            if switch in eval_nic:
                self.nic = eval_nic[switch]
            else:
                self.logger.error(
                    'Failed to get coprocessor nic for the switch: {0}'.format(switch))
        except ValueError:
            self.nic = nic
        self.interval = str(self.controller['reinvestigation_frequency'])
        self.iterations = str(iterations)

    def start_coprocessor(self):
        '''
        Starts coprocessor for a given endpoint with the
        options passed in at the creation of the class instance.
        '''
        status = False
        payload = {
            'nic': self.nic,
            'id': self.id,
            'interval': self.interval,
            'filter': '\'ether host {0}\''.format(self.mac),
            'iters': self.iterations,
            'metadata': "{'endpoint_data': " + str(self.endpoint.endpoint_data) + '}'}

        self.logger.debug('Payload: {0}'.format(str(payload)))

        network_tap_addr = self.controller['network_tap_ip'] + \
            ':' + self.controller['network_tap_port']
        uri = 'http://' + network_tap_addr + '/create'

        try:
            resp = requests.post(uri, data=json.dumps(payload))
            # TODO improve logged output
            self.logger.debug(
                'Collector response: {0}'.format(resp.text))
            response = ast.literal_eval(resp.text)
            if response[0]:
                self.logger.info(
                    'Successfully started the collector for: {0}'.format(self.id))
                self.endpoint.endpoint_data['container_id'] = response[1].rsplit(
                    ':', 1)[-1].strip()
                status = True
            else:
                self.logger.error(
                    'Failed to start collector because: {0}'.format(response[1]))
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Failed to start collector because: {0}'.format(str(e)))
        return status

    def stop_coprocessor(self):
        '''
        Stops coprocessor for a given endpoint.
        '''
        status = False
        if 'container_id' not in self.endpoint.endpoint_data:
            self.logger.warning(
                'No collector to stop because no container_id for endpoint')
            return True

        payload = {'id': [self.endpoint.endpoint_data['container_id']]}
        self.logger.debug('Payload: {0}'.format(str(payload)))

        network_tap_addr = self.controller['network_tap_ip'] + \
            ':' + self.controller['network_tap_port']
        uri = 'http://' + network_tap_addr + '/stop'

        try:
            resp = requests.post(uri, data=json.dumps(payload))
            self.logger.debug(
                'Collector response: {0}'.format(resp.text))
            response = ast.literal_eval(resp.text)
            if response[0]:
                self.logger.info(
                    'Successfully stopped the collector for: {0}'.format(self.id))
                status = True
            else:
                self.logger.error(
                    'Failed to stop collector because response failed with: {0}'.format(response[1]))
        except Exception as e:  # pragma: no cover
            self.logger.error(
                'Failed to stop collector because: {0}'.format(str(e)))
        return status

    