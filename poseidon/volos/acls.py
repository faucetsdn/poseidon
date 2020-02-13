# -*- coding: utf-8 -*-
"""
Created on 31 January 2020
@author: Ryan Ashley
"""
import json
import logging
import os
import yaml

from pathlib import Path

class Acl(object):

  def __init__(self, endpoint, acl_dir, copro_vlan=2, copro_port=23):
        self.logger = logging.getLogger('coprocessor')
        self.endpoint = endpoint
        self.id = endpoint.name
        self.mac = endpoint.endpoint_data['mac']
        self.copro_vlan = copro_vlan
        self.copro_port = copro_port
        self.acl_dir = acl_dir
        self.acl_key = f"volos_copro_{self.mac}"
        self.acl_file = os.path.join(self.acl_dir, f"/volos_copro_{self.mac}.yaml")
          
    
  def write_acl_file(self, port_list=[]):
    acls = { }
    acls[self.acl_key] = []
    status = False
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
          acls[self.acl_key].append(rule)
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
            acls[self.acl_key].append(rule)
    acls[self.acl_key].append({'rule':{'actions': {'allow': 1}}})
    try:
      with open(self.acl_file, 'w') as acl_file:
          status = yaml.dump({'acls': acls}, acl_file)
    except Exception as e:  # pragma: no cover
      self.logger.error('Volos ACL file:{0} could not be written. Coprocessing may not work as expected'.format(self.acl_file))
      status = False
    return status

  def delete_acl_file(self):
    status = False
    try:
      if os.path.exists(self.acl_file):
        os.remove(self.acl_file)
        status = True
    except Exception as e:  # pragma: no cover
      self.logger.error('Volos ACL file:{0} could not be deleted. Coprocessing may not work as expected'.format(self.acl_file))
    return status

  def ensure_acls_dir(self):
    status = False
    try:
      if not os.path.exists(self.acl_dir):
        Path(self.acl_dir).mkdir(parents=True, exist_ok=True)
        status = True
    except Exception as e:  # pragma: no cover
      self.logger.error('Volos ACL directory:{0} could not be created. Coprocessing may not work as expected'.format(self.acl_file))
      status = False

    return status