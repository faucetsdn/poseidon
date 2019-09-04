# -*- coding: utf-8 -*-
"""
Created on 9 December 2018
@author: Charlie Lewis
"""
from poseidon.helpers.collector import Collector


class Actions(object):

    def __init__(self, endpoint, sdnc):
        self.endpoint = endpoint
        self.sdnc = sdnc

    def shutdown_endpoint(self):
        ''' tell the controller to shutdown an endpoint '''
        if self.sdnc:
            self.sdnc.shutdown_endpoint()
        return

    def mirror_endpoint(self):
        '''
        tell vent to start a collector and the controller to begin
        mirroring traffic
        '''
        status = False
        if self.sdnc:
            if self.sdnc.mirror_mac(self.endpoint.endpoint_data['mac'], self.endpoint.endpoint_data['segment'], self.endpoint.endpoint_data['port']):
                status = Collector(
                    self.endpoint, self.endpoint.endpoint_data['segment']).start_vent_collector()
        else:
            status = True
        return status

    def unmirror_endpoint(self):
        ''' tell the controller to unmirror traffic '''
        status = False
        if self.sdnc:
            if self.sdnc.unmirror_mac(self.endpoint.endpoint_data['mac'], self.endpoint.endpoint_data['segment'], self.endpoint.endpoint_data['port']):
                status = Collector(
                    self.endpoint, self.endpoint.endpoint_data['segment']).stop_vent_collector()
        else:
            status = True
        return status

    def update_acls(self, rules_file=None, endpoints=None):
        ''' tell the controller what ACLs to dynamically change '''
        status = False
        if self.sdnc:
            status = self.sdnc.update_acls(
                rules_file=rules_file, endpoints=endpoints)
            status = True
        return status
