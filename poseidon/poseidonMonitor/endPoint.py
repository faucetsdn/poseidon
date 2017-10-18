#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Created on 2 October 2017
@author: Jorissss
"""

import hashlib
import json

class EndPoint:
    def __init__(self, data, state='NONE', next_state='NONE'):
        self.state = state
        self.next_state = next_state
        self.data = dict(data)

    def make_hash(self):
        ''' hash the metadata in a sane way '''
        h = hashlib.new('ripemd160')
        pre_h = str()
        post_h = None
        # nodhcp -> dhcp withname makes different hashes
        # {u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': None, u'ip-address': u'10.179.0.100'}}^
        # {u'tenant': u'FLOORPLATE', u'mac': u'ac:87:a3:2b:7f:12', u'segment': u'prod', u'name': u'demo-laptop', u'ip-address': u'10.179.0.100'}}
        # ^^^ make different hashes if name is included
        # for word in ['tenant', 'mac', 'segment', 'name', 'ip-address']:

        for word in ['tenant', 'mac', 'segment', 'ip-address']:
            pre_h = pre_h + str(self.data.get(str(word), 'missing'))
        h.update(pre_h.encode('utf-8'))
        post_h = h.hexdigest()
        return post_h

    def to_str(self):
        '''make string representation of internals of object'''
        strep = 'state: ' + self.state
        strep += ', next_state: ' + self.next_state
        strep += ', data: ' + str(self.data)
        return strep

    def to_json(self):
        '''return a json view of the object'''
        return json.dumps({ 'endpoint_data': self.data
                          , 'state': self.state
                          , 'next_state': self.next_state })

    @classmethod
    def from_json(cls, json_obj):
        '''initialize object from json'''
        obj_dict = json.loads(json_obj)
        return cls(obj_dict['endpoint_data'], obj_dict['state'], obj_dict['next_state'])

    def update_state(self, next_s='NONE'):
        '''state <- next_state, next_state <- 'NONE' or a string that is passed as a parameter'''
        self.state = self.next_state
        self.next_state = next_s
