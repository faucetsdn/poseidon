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
        controller = {'URI': None,
                      'USER': None,
                      'PASS': None,
                      'TYPE': None,
                      'SPAN_FABRIC_NAME': 'vent',
                      'INTERFACE_GROUP': 'ig1',
                      'CONFIG_FILE': None,
                      'LOG_FILE': None,
                      'MIRROR_PORTS': None,
                      'RABBIT_ENABLED': False,
                      'LEARN_PUBLIC_ADDRESSES': False,
                      'reinvestigation_frequency': 900,
                      'max_concurrent_reinvestigations': 2
                      }

        for section in self.config.sections():
            for key in self.config[section]:
                val = self.config[section][key]
                if key == 'controller_type':
                    controller['TYPE'] = val
                elif key == 'controller_uri':
                    controller['URI'] = val
                elif key == 'controller_user':
                    controller['USER'] = val
                elif key == 'controller_pass':
                    controller['PASS'] = val
                elif key == 'controller_span_fabric_name':
                    controller['SPAN_FABRIC_NAME'] = val
                elif key == 'controller_interface_group':
                    controller['INTERFACE_GROUP'] = val
                elif key == 'trust_self_signed_cert':
                    try:
                        controller['TRUST_SELF_SIGNED_CERT'] = ast.literal_eval(
                            val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'learn_public_addresses':
                    try:
                        controller['LEARN_PUBLIC_ADDRESSES'] = ast.literal_eval(
                            val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'controller_config_file':
                    controller['CONFIG_FILE'] = val
                elif key == 'controller_log_file':
                    controller['LOG_FILE'] = val
                elif key == 'collector_nic':
                    try:
                        controller['collector_nic'] = ast.literal_eval(val)
                    except ValueError:
                        controller['collector_nic'] = val
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'controller_mirror_ports':
                    try:
                        controller['MIRROR_PORTS'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'rabbit_enabled':
                    try:
                        controller['RABBIT_ENABLED'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'FA_RABBIT_ENABLED':
                    try:
                        controller['FA_RABBIT_ENABLED'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'FA_RABBIT_PORT':
                    try:
                        controller['FA_RABBIT_PORT'] = int(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'scan_frequency':
                    try:
                        controller['scan_frequency'] = int(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'reinvestigation_frequency':
                    try:
                        controller['reinvestigation_frequency'] = int(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'max_concurrent_reinvestigations':
                    try:
                        controller['max_concurrent_reinvestigations'] = int(
                            val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'ignore_vlans':
                    try:
                        controller['ignore_vlans'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'ignore_ports':
                    try:
                        controller['ignore_ports'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                elif key == 'trunk_ports':
                    try:
                        controller['trunk_ports'] = ast.literal_eval(val)
                    except Exception as e:  # pragma: no cover
                        self.logger.error(
                            'Unable to set configuration option {0} because {1}'.format(key, str(e)))
                else:
                    controller[key] = val
        return controller
