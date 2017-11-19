#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
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
Created on 19 November 2017
@author: cglewis
"""
from yaml import load, dump
from yaml import CLoader as Loader, CDumper as Dumper

from poseidon.baseClasses.Logger_Base import Logger

module_logger = Logger.logger


class Parser:

    def __init__(self):
        self.logger = module_logger

    def config(self, config_file):
        stream = open(config_file, 'r')
        document = dump(load(stream), default_flow_style=False)
        self.logger.info(document)

    def log(self, log_file):
        pass

