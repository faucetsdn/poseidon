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
Created on 17 August 2016
@author: aganeshLab41, tlanham

Test module for machine learning plugin
for classifying ports from tcp packets.
"""
import pytest
import sys
import os

from port_classifier import rabbit_init
from port_classifier import get_path
from port_classifier import get_host
from port_classifier import save_model


def test_get_path():
    get_path()
    sys.argv = []
    get_path()


def test_get_host():
    get_host()
    os.environ['POSEIDON_HOST'] = '1.1.1.1'
    assert get_host() == '1.1.1.1'


class Test:
    def __init__(self):
        self.s = 'hello world'


def test_save_model():
    model = Test()
    save_model(model)
    assert os.path.isfile('port_class_log_reg_model.pickle')
    os.environ['POSEIDON_HOST'] = 'httpbin.org/post'
    save_model(model)


@pytest.mark.skip(reason='requires rabbitmq broker, integration test')
def test_rabbit_init():
    channel, connection = rabbit_init(host='poseidon-rabbit',
                                      exchange='topic-poseidon-internal',
                                      queue_name='features_flowparser',
                                      rabbit_rec=False)
