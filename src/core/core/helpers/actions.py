# -*- coding: utf-8 -*-
"""
Created on 9 December 2018
@author: Charlie Lewis
"""
from poseidon_core.helpers.collector import Collector
from poseidon_core.operations.volos.acls import VolosAcl


class Actions:

    def __init__(self, endpoint, sdnc):
        self.endpoint = endpoint
        self.sdnc = sdnc

    def mirror_endpoint(self):
        '''
        tell network_tap to start a collector and the controller to begin
        mirroring traffic
        '''
        status = False
        if self.sdnc:
            endpoint_data = self.endpoint.endpoint_data
            if self.sdnc.mirror_mac(endpoint_data['mac'], endpoint_data['segment'], endpoint_data['port']):
                collector = Collector(self.endpoint, endpoint_data['segment'])
                if collector.nic:
                    status = collector.start_collector()
        else:
            status = True
        return status

    def unmirror_endpoint(self):
        ''' tell the controller to unmirror traffic '''
        status = False
        if self.sdnc:
            endpoint_data = self.endpoint.endpoint_data
            if self.sdnc.unmirror_mac(endpoint_data['mac'], endpoint_data['segment'], endpoint_data['port']):
                collector = Collector(self.endpoint, endpoint_data['segment'])
                if collector.nic:
                    status = collector.stop_collector()
        else:
            status = True
        return status

    def coprocess_endpoint(self):
        '''
        Build up and apply acls for coprocessing
        '''
        status = False
        if self.sdnc:
            endpoint_data = self.endpoint.endpoint_data
            if self.sdnc.volos and self.sdnc.volos.enabled:
                acl = VolosAcl(
                    self.endpoint, acl_dir=self.sdnc.volos.acl_dir,
                    copro_vlans=[self.sdnc.volos.copro_vlan], copro_port=self.sdnc.volos.copro_port)
                endpoints = [self.endpoint]
                force_apply_rules = [acl.acl_key]
                coprocess_rules_files = [acl.acl_file]
                port_list = self.sdnc.volos.get_port_list(
                    endpoint_data['mac'], ipv4=endpoint_data.get('ipv4', None), ipv6=endpoint_data.get('ipv6', None))
                if acl.ensure_acls_dir() and acl.write_acl_file(port_list):
                    status = self.sdnc.update_acls(
                        rules_file=None, endpoints=endpoints,
                        force_apply_rules=force_apply_rules, coprocess_rules_files=coprocess_rules_files)
            else:
                status = True
        return status

    def uncoprocess_endpoint(self):
        ''' tell the controller to remove coprocessing acls'''
        status = False
        if self.sdnc:
            if self.sdnc.volos and self.sdnc.volos.enabled:
                acl = VolosAcl(
                    self.endpoint, acl_dir=self.sdnc.volos.acl_dir,
                    copro_vlans=[self.sdnc.volos.copro_vlan], copro_port=self.sdnc.volos.copro_port)
                endpoints = [self.endpoint]
                force_remove_rules = [acl.acl_key]
                if self.sdnc.update_acls(
                        rules_file=None, endpoints=endpoints,
                        force_remove_rules=force_remove_rules, coprocess_rules_files=None):
                    status = acl.delete_acl_file()
        else:
            status = True
        return status

    def update_acls(self, rules_file=None, endpoints=None, force_apply_rules=None, force_remove_rules=None):
        ''' tell the controller what ACLs to dynamically change '''
        status = False
        if self.sdnc:
            status = self.sdnc.update_acls(
                rules_file=rules_file, endpoints=endpoints,
                force_apply_rules=force_apply_rules, force_remove_rules=force_remove_rules)
        return status
