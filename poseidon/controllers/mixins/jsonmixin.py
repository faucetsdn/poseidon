# -*- coding: utf-8 -*-
"""
Created on 25 July 2016
@author: kylez
"""
import json
import logging

import requests


class JsonMixin:

    @staticmethod
    def parse_json(response):
        """
        Parse JSON from the `text` field of a response.
        """
        logger = logging.getLogger('requests')
        if response.status_code != requests.codes.ok:
            logger.error('Request failed: {0} {1} {2}'.format(
                response.status_code, response.url, response.text))
        else:
            logger.debug('Request succeeded: {0} {1}'.format(
                response.status_code, response.url))
        if not response.text:
            return json.loads('{}')
        return response.json()
