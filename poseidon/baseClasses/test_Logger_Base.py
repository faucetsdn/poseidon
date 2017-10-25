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
Test module for poseidonMonitor.py

Created on 25 Oct 2017
@author: dgrossman
"""

import json
from os import getenv

from poseidon.baseClasses.Logger_Base import Logger

#import logging
#import logging.handlers
#import os
#import socket


def test_logger_base():
    class MockLogger(Logger):
        def __init__(self):
            pass
    path = getenv('POSEIDON_LOGGER')

    logger = MockLogger()
    config = ''
    with open(path, 'rt') as f:
        config = json.load(f)

    logger.logger_config(None) 
    logger.logger_config(config)
