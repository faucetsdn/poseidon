# -*- coding: utf-8 -*-
"""
Created on 25 July 2016
@author: kylez
"""
import json


class JsonMixin:

    @staticmethod
    def parse_json(response):
        """
        Parse JSON from the `text` field of a response.
        """
        if not response.text:
            return json.loads('{}')
        return response.json()
