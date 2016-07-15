#!/usr/bin/env python
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
Test module for poseidonMain.py

Created on 15 July 2016
@author: dgrossman
"""
import os

import pytest
from Config import config_interface


def test_env():
    """
    Tests goTime
    """
    expected = None
    try:
        expected = os.environ['POSEIDON_CONFIG_URL']
    except KeyError:
        pass

    a = config_interface

    assert a.URL == expected


def test_get_BADsection():
    expected = None
    try:
        expected = os.environ['POSEIDON_CONFIG_URL']
    except KeyError:
        pass

    a = config_interface.get_section('DOESNOTEXIST')

    if expected is not None:
        assert a == """['"Failed to find section: DOESNOTEXIST"']"""
    else:
        assert a is None


def test_get_GOODsection():
    expected = None
    try:
        expected = os.environ['POSEIDON_CONFIG_URL']
    except KeyError:
        pass

    a = config_interface.get_section('PoseidonMain:Config')

    if expected is not None:
        assert a == """['[["config", "True"]]']"""
    else:
        assert a is None
