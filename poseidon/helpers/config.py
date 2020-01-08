# -*- coding: utf-8 -*-
"""
Created on 5 December 2018
@author: Charlie Lewis
"""

import ast
import configparser
import logging
import os
import netifaces  # pytype: disable=import-error


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
            'URI': None,
            'USER': None,
            'PASS': None,
            'TYPE': None,
            'SPAN_FABRIC_NAME': 'vent',
            'INTERFACE_GROUP': 'ig1',
            'CONFIG_FILE': None,
            'LOG_FILE': None,
            'RULES_FILE': None,
            'MIRROR_PORTS': None,
            'AUTOMATED_ACLS': False,
            'RABBIT_ENABLED': False,
            'LEARN_PUBLIC_ADDRESSES': False,
            'reinvestigation_frequency': 900,
            'max_concurrent_reinvestigations': 2,
            'logger_level': 'INFO',
        }

        def valid_interface(name):
            if name in netifaces.interfaces():
                return name
            raise Exception('no such interface: %s' % name)

        config_map = {
            'controller_type': ('TYPE', []),
            'controller_uri': ('URI', []),
            'controller_user': ('USER', []),
            'controller_pass': ('PASS', []),
            'controller_span_fabric_name': ('SPAN_FABRIC_NAME', []),
            'controller_interface_group': ('INTERFACE_GROUP', []),
            'trust_self_signed_cert': ('TRUST_SELF_SIGNED_CERT', [ast.literal_eval]),
            'learn_public_addresses': ('LEARN_PUBLIC_ADDRESSES', [ast.literal_eval]),
            'controller_config_file': ('CONFIG_FILE', []),
            'controller_log_file': ('LOG_FILE', []),
            'rules_file': ('RULES_FILE', []),
            'collector_nic': ('collector_nic', [valid_interface]),
            'controller_mirror_ports': ('MIRROR_PORTS', [ast.literal_eval]),
            'automated_acls': ('AUTOMATED_ACLS', [ast.literal_eval]),
            'rabbit_enabled': ('RABBIT_ENABLED', [ast.literal_eval]),
            'FA_RABBIT_ENABLED': ('FA_RABBIT_ENABLED', [ast.literal_eval]),
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
