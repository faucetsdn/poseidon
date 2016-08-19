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

Created on 29 May 2016
@author: dgrossman, tlanham
"""
import logging
from os import environ

import pytest
from poseidonMain import main
from poseidonMain import PoseidonMain

module_logger = logging.getLogger('poseidonMain.test_poseidonMain')


def test_poseidonMain_goTime():
    """
    Tests goTime
    """

    a = PoseidonMain()


# @pytest.mark.skip(reason='requires rabbitmq broker, integration test')
def test_poseidonMain_main(skipRabbit=True):
    a = main()
    assert a
