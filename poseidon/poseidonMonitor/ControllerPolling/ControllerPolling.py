#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.Poll2Callback#
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
Test module for Action.py

Created on 5 July 2016
@author: dgrossman
"""
import json

import falcon
import pytest


class ControllerPolling:
    """query the switch to determine if anything has changed,
       this functionality is needed as we do not want to modify
       a controller."""

    def __init__(self):
        self.retval = {}
        self.times = 0

    def on_get(self, req, resp):
        """Haneles Get requests"""
        # TODO make calls to get switch state,
        # TODO compare to previous switch state
        # TODO schedule something to occur for updated flows
        self.retval['times'] = self.times
        # TODO change response to something reflecting success of traversal
        self.retval['resp'] = 'ok'
        self.times = self.times + 1
        resp.body = json.dumps(self.retval)
