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
'''
Test module for Config.py

Created on 28 June 2016
@author: dgrossman, lanhamt
'''
import hashlib
import json

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.Config.Config import config_interface


# exposes the application for testing

def test_config_full_get():
    h = hashlib.new('sha256')

    '''
    Tests retrieving the entire config file.
    '''
    resp = config_interface.get_endpoint('Handle_FullConfig').direct_get()
    h.update(resp.encode('utf-8'))


def test_config_section_get_FAIL():
    resp = config_interface.get_endpoint(
        'Handle_SectionConfig').direct_get('not_a_section')
    assert resp == 'Failed to find section: not_a_section'


def test_config_field_get_4F():
    '''
    Tests retrieving field from a section in the config file.
    '''
    resp = config_interface.get_endpoint(
        'Handle_FieldConfig').direct_get('not_a_key', 'bad_section')
    assert resp == 'Can\'t find field: not_a_key in section: bad_section'


def test_selfconfig():
    '''
    Tests self configuration
    '''
    config_interface.configure()
