# -*- coding: utf-8 -*-
"""
Created on 05 February 2020
@author: Ryan Ashley
"""
import os
import json
import yaml
import logging


#from poseidon.constants import PROTOCOL_MAP
PROTOCOL_MAP = {
    'tcp': 6,
    'udp': 17
}

class Volos(object):
    def __init__(self, controller):
        self.logger = logging.getLogger('volos')
        self.enabled = controller['enable_volos']
        self.coprocessor_nic = controller['coprocessor_nic']
        self.coprocessor_port = controller['coprocessor_port']
        self.coprocessor_vlan = controller['coprocessor_vlan']
        self.coprocessing_frequency = controller['coprocessing_frequency']
        self.ignore_copro_ports = controller['ignore_copro_ports']
        self.acl_dir = controller['acl_dir']
        volos_cfg_file = controller['volos_cfg_file']
        self.container_config = self.parse_volos_cfg(volos_cfg_file)

    def parse_volos_cfg(self, volos_cfg_file):
        cfg = None
        container_cfg = None
        if os.path.exists(volos_cfg_file): 
            try:
                with open(volos_cfg_file, 'r') as f:
                    cfg = yaml.safe_load(f)
            except Exception as e:  # pragma: no cover
                self.logger.error('Volos configuration could not be loaded. disabling volos')
                self.logger.error(
                        'Failed to load volos config with error: {0}'.format(str(e)))
                self.enabled = False
            container_cfg = []
            if cfg:
                for repo in cfg:
                    item ={}
                    for name in cfg[repo]:
                        item['repo'] = repo
                        item['name'] = name
                        item['branch'] = cfg[repo][name]['branch']
                        item['build'] = cfg[repo][name]['build']
                        item['start'] = cfg[repo][name]['start']
                        item['ports'] = []
                        for port in cfg[repo][name]['ports']:
                            cfg_p = {}
                            cfg_p['proto'] = port['port']['protocol']
                            cfg_p['proto_id'] = PROTOCOL_MAP[port['port']['protocol']]
                            mapping = port['port']['mapping']
                            cfg_p['host'] = mapping[:mapping.index(":")]
                            cfg_p['dest'] = mapping[mapping.index(":"):]
                            item['ports'].append(cfg_p)

                    container_cfg.append(item)

            else:
                self.enabled = False
        else:
            self.logger.error('Volos configuration could not found. disabling volos')
            self.enabled = False

        return container_cfg

    '''
    build structure of the form 
    {
    'mac1': {
        'ip': {
         'v4': "ipv4_1",
         'v6': "ipv6_1",
        },
        'ports': [
            {
                'proto': 'tcp',
                'proto_id': 6,
                'port': 25,
            },
            {
                'proto': 'tcp',
                'proto_id': 6,
                'port': 26,
            },
            {
                'proto': 'udp',
                'proto_id': 17,
                'port': 27,
            }
        ]
    },
    '''
    def get_port_list(self, mac, ipv4=None, ipv6=None):
        port_list ={}
        port_list[mac] ={
            'ip':{
                'v4': ipv4,
                'v6': ipv6
            },
            'ports':[]
        }
        for i in self.container_config:
            for port in i['ports']:
                p = {}
                p['proto'] = port['proto']
                p['proto_id'] = port['proto_id']
                p['port'] = port['dest']

                port_list[mac]['ports'].append(p)

        return port_list

