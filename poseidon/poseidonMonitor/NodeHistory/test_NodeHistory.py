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
Test module for NodeHistory.py
Created on 28 June 2016
@author: dgrossman, lanhamt
"""
import logging

import falcon
import pytest
from NodeHistory import Handle_Default
from NodeHistory import NodeHistory
from NodeHistory import nodehistory_interface

module_logger = logging.getLogger(__name__)

application = falcon.API()
application.add_route('/v1/history/{resource}',
                      nodehistory_interface.get_endpoint('Handle_Default'))


def test_node_hist_class():
    nh = NodeHistory()
    nh.add_endpoint('Handle_Default', Handle_Default)
    nh.configure()
    nh.configure_endpoints()


def test_handle_default_class():
    hd = Handle_Default()
    hd.owner = Handle_Default()
    hd.configure()
    assert hd.owner


# exposes the application for testing
@pytest.fixture
def app():
    return application


def test_pcap_resource_get(client):
    """
    Tests the Hisotry class
    """
    resp = client.get('/v1/history/someHistoryRequest')
    assert resp.status == falcon.HTTP_OK
