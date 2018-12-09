# -*- coding: utf-8 -*-
''' Created on 9 December 2018
@author: Charlie Lewis
'''
import ast
import json

import requests

from p.helpers.config import Config
from p.helpers.log import Logger


class Collector(object):

    def __init__(self, endpoint, iterations=1):
        self.logger = Logger.logger
        self.poseidon_logger = Logger.poseidon_logger
        self.controller = Config().get_config()
        self.endpoint = endpoint
        self.id = endpoint.name
        self.mac = endpoint.endpoint_data['mac']
        self.endpoint_data = endpoint.endpoint_data
        self.nic = self.controller['collector_nic']
        self.interval = self.controller['reinvestigation_frequency']
        self.iterations = iterations

    def start_vent_collector(self):
        '''
        Starts vent collector for a given device with the
        options passed in at the creation of the class instance.
        '''
        payload = {
            'nic': self.nic,
            'id': self.id,
            'interval': self.interval,
            'filter': '\'ether host {0}\''.format(self.mac),
            'iters': self.iterations,
            'metadata': str(self.endpoint_data)}

        self.poseidon_logger.debug('vent payload: ' + str(payload))

        vent_addr = self.controller['vent_ip'] + \
            ':' + self.controller['vent_port']
        uri = 'http://' + vent_addr + '/create'

        try:
            resp = requests.post(uri, data=json.dumps(payload))
            self.poseidon_logger.debug(
                'collector response: ' + resp.text)
        except Exception as e:  # pragma: no cover
            self.poseidon_logger.debug(
                'failed to start vent collector' + str(e))
        return

    # returns a dictionary of existing collectors keyed on dev_hash
    def get_vent_collectors(self):
        vent_addr = self.controller['vent_ip'] + \
            ':' + self.controller['vent_port']
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
                    # TODO
                    # coll = Collector(item['id'], item['args'][0], item['args'][1],
                    #                 item['args'][2], item['args'][3], host, item['status'])
                    #collectors.update({coll.hash: coll})
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
