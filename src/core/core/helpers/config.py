# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""
import ast
import configparser
import json
import logging
import os


class Config():

    def __init__(self):
        self.logger = logging.getLogger('config')
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        if os.environ.get('POSEIDON_CONFIG') is not None:
            self.config_path = os.environ.get('POSEIDON_CONFIG')
        else:  # pragma: no cover
            raise Exception(
                'Could not find poseidon config. Make sure to set the POSEIDON_CONFIG environment variable')
        self.config.read_file(open(self.config_path, 'r'))

    def get_config(self):
        # set some defaults
        controller = {
            'TYPE': None,
            'RULES_FILE': None,
            'MIRROR_PORTS': None,
            'AUTOMATED_ACLS': False,
            'LEARN_PUBLIC_ADDRESSES': False,
            'reinvestigation_frequency': 900,
            'max_concurrent_reinvestigations': 2,
            'max_concurrent_coprocessing': 2,
            'logger_level': 'INFO',
            'faucetconfrpc_address': 'faucetconfrpc:59999',
            'faucetconfrpc_client': 'faucetconfrpc',
            'prometheus_ip': 'prometheus',
            'prometheus_port': 9090,
        }

        config_map = {
            'controller_type': ('TYPE', []),
            'learn_public_addresses': ('LEARN_PUBLIC_ADDRESSES', [ast.literal_eval]),
            'rules_file': ('RULES_FILE', []),
            'collector_nic': ('collector_nic', []),
            'controller_mirror_ports': ('MIRROR_PORTS', [json.loads]),
            'controller_proxy_mirror_ports': ('controller_proxy_mirror_ports', [json.loads]),
            'tunnel_vlan': ('tunnel_vlan', [int]),
            'tunnel_name': ('tunnel_name', []),
            'automated_acls': ('AUTOMATED_ACLS', [ast.literal_eval]),
            'FA_RABBIT_PORT': ('FA_RABBIT_PORT', [int]),
            'scan_frequency': ('scan_frequency', [int]),
            'reinvestigation_frequency': ('reinvestigation_frequency', [int]),
            'max_concurrent_reinvestigations': ('max_concurrent_reinvestigations', [int]),
            'max_concurrent_coprocessing': ('max_concurrent_coprocessing', [int]),
            'ignore_vlans': ('ignore_vlans', [json.loads]),
            'ignore_ports': ('ignore_ports', [json.loads]),
            'trunk_ports': ('trunk_ports', [json.loads]),
            'logger_level': ('logger_level', []),
        }

        for section in self.config.sections():
            for key, val in self.config[section].items():
                if isinstance(val, str):
                    val = val.strip("'")
                controller_key, val_funcs = config_map.get(key, (key, []))
                for val_func in val_funcs:
                    try:
                        val = val_func(val)
                        break
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} {1} because {2}'.format(key, val, str(e)))
                controller[controller_key] = val
        return controller
