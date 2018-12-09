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
        ''' tell the controller to shutdown an endpoint by hash '''
        if my_hash in self.endpoints.state:
            my_ip = self.endpoints.get_endpoint_ip(my_hash)
            next_state = self.endpoints.get_endpoint_next(my_hash)
            self.sdnc.shutdown_ip(my_ip)
            self.endpoints.change_endpoint_state(my_hash)
            self.poseidon_logger.debug(
                'endpoint:{0}:{1}:{2}'.format(my_hash, my_ip, next_state))
            return True
        return False

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
        if my_hash in self.endpoints.state:
            my_mac = self.endpoints.get_endpoint_mac(my_hash)
            my_ip = self.endpoints.get_endpoint_ip(my_hash)
            next_state = self.endpoints.get_endpoint_next(my_hash)
            self.sdnc.unmirror_mac(my_mac, messages=messages)
            self.endpoints.reset_mirror_timer(my_hash)
            self.poseidon_logger.debug(
                'endpoint:{0}:{1}:{2}:{3}'.format(my_hash, my_mac, my_ip, next_state))
            return True
        return False
