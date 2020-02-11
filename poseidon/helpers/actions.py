# -*- coding: utf-8 -*-
"""
Created on 9 December 2018
@author: Charlie Lewis
"""
from poseidon.helpers.collector import Collector
from poseidon.volos.coprocessor import Coprocessor
from poseidon.volos.acls import Acl


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
        tell network_tap to start a collector and the controller to begin
        mirroring traffic
        '''
        status = False
        if self.sdnc:
            if self.sdnc.mirror_mac(self.endpoint.endpoint_data['mac'], self.endpoint.endpoint_data['segment'], self.endpoint.endpoint_data['port']):
                status = Collector(
                    self.endpoint, self.endpoint.endpoint_data['segment']).start_collector()
        else:
            status = True
        return status

    def unmirror_endpoint(self):
        ''' tell the controller to unmirror traffic '''
        status = False
        if self.sdnc:
            if self.sdnc.unmirror_mac(self.endpoint.endpoint_data['mac'], self.endpoint.endpoint_data['segment'], self.endpoint.endpoint_data['port']):
                status = Collector(
                    self.endpoint, self.endpoint.endpoint_data['segment']).stop_collector()
        else:
            status = True
        return status

    def coprocess_endpoint(self):
        '''
        Build up and apply acls for coprocessing
        '''
        status = False
        if self.sdnc:
            if self.sdnc.volos and self.sdnc.volos.enabled:
                acl = Acl(self.endpoint, acl_dir=self.sdnc.volos.acl_dir, copro_vlan=self.sdnc.volos.copro_vlan, copro_port=self.sdnc.volos.copro_port)
                endpoints = [self.endpoint]
                force_apply_rules = [acl.acl_key]
                coprocess_rules_files = [acl.acl_file]
                port_list = self.sdnc.volos.get_port_list(self.endpoint.endpoint_data['mac'], ipv4=self.endpoint.endpoint_data.get('ipv4', None), ipv6=self.endpoint.endpoint_data.get('ipv6', None))
                if acl.ensure_acl_dir() and acl.write_acl_file(port_list):
                    status = self.sdnc.update_acls(
                        rules_file=None, endpoints=endpoints, force_apply_rules=force_apply_rules, coprocess_rules_files=coprocess_rules_files)
            else:
                status = True
        return status

    def uncoprocess_endpoint(self):
        ''' tell the controller to remove coprocessing acls'''
        status = False
        if self.sdnc:
            if self.sdnc.volos and self.sdnc.volos.enabled:
                acl = Acl(self.endpoint, acl_dir=self.sdnc.volos.acl_dir, copro_vlan=self.sdnc.volos.copro_vlan, copro_port=self.sdnc.volos.copro_port)
                endpoints = [self.endpoint]
                force_remove_rules = [acl.acl_key]
                if self.sdnc.update_acls(
                        rules_file=None, endpoints=endpoints, force_remove_rules=force_remove_rules, coprocess_rules_files=None) :
                    status = acl.delete_acl_file()
        else:
            status = True
        return status

    def update_acls(self, rules_file=None, endpoints=None, force_apply_rules=None, force_remove_rules=None):
        ''' tell the controller what ACLs to dynamically change '''
        status = False
        if self.sdnc:
            status = self.sdnc.update_acls(
                rules_file=rules_file, endpoints=endpoints, force_apply_rules=force_apply_rules, force_remove_rules=force_remove_rules)
        return status
