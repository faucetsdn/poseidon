"""
Created on 2 October 2017
@author: Jorissss
"""

import hashlib
import json



class EndPoint:
    def __init__(self, data):
        self.state = 'NONE'
        self.next_state = 'NONE'
        self.data = dict(data)

    @staticmethod
    def make_hask(self):
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
        h.update(pre_h)
        post_h = h.hexdigest()
        return post_h

    def to_str(self):
        '''make string representation of internals of object'''
        strep = 'state: ' + self.state + '\n'
        strep += 'next_state: ' + self.next_state + '\n'
        strep += 'data: ' + str(self.data)
        return strep

    def to_json(self):
        '''return a json view of the object'''
        return json.dumps(self.data)

    @classmethod
    def from_json(cls, json_obj):
        '''initialize object from json'''
        return cls(json.loads(json_obj))

    def update_state(self, next_s='NONE'):
        '''state <- next_state, next_state <- 'NONE' or a string that is passed as a parameter'''
        self.state = self.next_state
        self.next_state = next_s
