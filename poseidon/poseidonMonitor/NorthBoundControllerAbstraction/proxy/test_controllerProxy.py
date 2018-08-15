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
Test module for controllerproxy.

@author: kylez
"""
#import logging
from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.controllerproxy import ControllerProxy


def test_ControllerProxy():
    """
    Tests ControllerProxy
    # http://jsonplaceholder.typicode.com: Fake online REST API for testing.
    """
    proxy = ControllerProxy('http://jsonplaceholder.typicode.com')
    r = proxy.get_resource('posts')
    r.raise_for_status()
    r = proxy.post_resource('posts')
    r.raise_for_status()
    r = proxy.request_resource(
        method='PUT',
        url='http://jsonplaceholder.typicode.com/posts/1')
    r.raise_for_status()
