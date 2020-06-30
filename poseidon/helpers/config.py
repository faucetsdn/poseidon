# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""
import ast
import configparser
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
            'CONFIG_FILE': None,
            'RULES_FILE': None,
            'MIRROR_PORTS': None,
            'AUTOMATED_ACLS': False,
            'LEARN_PUBLIC_ADDRESSES': False,
            'reinvestigation_frequency': 900,
            'max_concurrent_reinvestigations': 2,
            'logger_level': 'INFO',
            'faucetconfrpc_address': 'faucetconfrpc:59999'
        }

        config_map = {
            'controller_type': ('TYPE', []),
            'learn_public_addresses': ('LEARN_PUBLIC_ADDRESSES', [ast.literal_eval]),
            'controller_config_file': ('CONFIG_FILE', []),
            'rules_file': ('RULES_FILE', []),
            'collector_nic': ('collector_nic', []),
            'controller_mirror_ports': ('MIRROR_PORTS', [ast.literal_eval]),
            'tunnel_vlan': ('tunnel_vlan', [int]),
            'tunnel_name': ('tunnel_name', []),
            'automated_acls': ('AUTOMATED_ACLS', [ast.literal_eval]),
            'FA_RABBIT_PORT': ('FA_RABBIT_PORT', [int]),
            'scan_frequency': ('scan_frequency', [int]),
            'reinvestigation_frequency': ('reinvestigation_frequency', [int]),
            'max_concurrent_reinvestigations': ('max_concurrent_reinvestigations', [int]),
            'ignore_vlans': ('ignore_vlans', [ast.literal_eval]),
            'ignore_ports': ('ignore_ports', [ast.literal_eval]),
            'trunk_ports': ('trunk_ports', [ast.literal_eval]),
            'logger_level': ('logger_level', []),
        }

        for section in self.config.sections():
            for key in self.config[section]:
                controller_key, val_funcs = config_map.get(key, (key, []))
                val = self.config[section][key]
                if val_funcs:
                    # attempt to validate with function one at a time.
                    for val_func in val_funcs:
                        try:
                            controller[controller_key] = val_func(val)
                            break
                        except Exception as e:  # pragma: no cover
                            self.logger.error(
                                'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                else:
                    # no mapping defined.
                    controller[controller_key] = val
        return controller
