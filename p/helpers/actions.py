"""
Created on 9 December 2018
@author: Charlie Lewis
"""
from p.helpers.collector import Collector


class Actions(object):

    def __init__(self, endpoint, sdnc):
        self.endpoint = endpoint
        self.sdnc = sdnc

    def shutdown_endpoint(self):
        ''' tell the controller to shutdown an endpoint '''
        self.sdnc.shutdown_endpoint()
        return

    def mirror_endpoint(self):
        '''
        tell vent to start a collector and the controller to begin
        mirroring traffic
        '''
        Collector(self.endpoint).start_vent_collector()
        self.sdnc.mirror_mac(self.endpoint.endpoint_data['mac'])
        return

    def unmirror_endpoint(self):
        ''' tell the controller to unmirror traffic '''
        self.sdnc.unmirror_mac(self.endpoint.endpoint_data['mac'])
        return
