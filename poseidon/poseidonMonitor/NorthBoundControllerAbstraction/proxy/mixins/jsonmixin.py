#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""
Created on 25 July 2016
@author: kylez
"""
import json

from poseidon.baseClasses.Logger_Base import Logger
module_logger = Logger.logger


class JsonMixin:

    @staticmethod
    def parse_json(response):
        """
        Parse JSON from the `text` field of a response.
        """
        if not response.text:
            return json.loads("{}")
        return response.json()
