# -*- coding: utf-8 -*-
"""
Created on 31 January 2020
@author: Ryan Ashley
"""
import json
import logging
import yaml

class Acls(object):

  def __init__(self, endpoint, acl_dir, copro_vlan=2, copro_port=23):
        self.logger = logging.getLogger('coprocessor')
        self.endpoint = endpoint
        self.id = endpoint.name
        self.mac = endpoint.endpoint_data['mac']
        self.copro_vlan = copro_vlan
        self.copro_port = copro_port
        self.acl_dir = acl_dir
    
  def write_acls(self, port_list=[]):
    acls = { }
    key = 'volos_copro_' + self.mac
    acls[key] = []
    for port in port_list:
      if 'ipv4_addresses' in self.endpoint.metadata:
        for ip in self.endpoint.metadata['ipv4_addresses']:
          rule = { 'rule': {
              'dl_type': 0x800, 
              'nw_proto': port['proto_id'], 
              'ipv4_src': ip,
              'actions': {
                'output': {
                  'ports': [self.copro_port], 
                  'vlan_vid': self.copro_vlan
                }
              }, 
          }}
          rule['rule'][port['proto']+ '_dst'] = port['port']
          acls[key].append(rule)
      if 'ipv6_addresses' in self.endpoint.metadata:
        for ip in self.endpoint.metadata['ipv6_addresses']:
            rule = { 'rule': {
                'dl_type': 0x86dd, 
                'nw_proto': port['proto_id'], 
                'ipv6_src': ip,
                'actions': {
                  'output': {
                    'ports': [self.copro_port], 
                    'vlan_vid': self.copro_vlan
                  }
                }, 
                
            }}
            rule['rule'][port['proto']+ '_dst'] = port['port']
            acls[key].append(rule)
    acls[key].append({'rule':{'actions': {'allow': 1}}})
    with open(f"{self.acl_dir}/volos_copro_{self.mac}", 'w') as acl_file:
        status = yaml.dump({'acls': acls}, acl_file)