#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Rest module for PoseidonConfig. Delivers
settings from the poseidon configuration
file.

Created on 17 May 2016
@author: dgrossman, lanhamt
"""
import configparser as ConfigParser
import json
import os

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.baseClasses.Monitor_Action_Base import Monitor_Action_Base
from poseidon.baseClasses.Monitor_Helper_Base import Monitor_Helper_Base


module_logger = Logger


class Config(Monitor_Action_Base):

    def __init__(self):
        super(Config, self).__init__()
        self.logger = module_logger.logger
        self.poseidon_logger = module_logger.poseidon_logger
        self.CONFIG = None
        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name
        self.mod_configuration = dict()

        self.config = ConfigParser.RawConfigParser()
        self.config.optionxform = str
        if os.environ.get('POSEIDON_CONFIG') is not None:
            self.config_path = os.environ.get('POSEIDON_CONFIG')
        else:
            raise Exception('Could not find poseidon config. Make sure to set the POSEIDON_CONFIG environment variable')
        self.config.readfp(open(self.config_path, 'r'))

    def configure(self):
        ostr = '{0}:configure'.format(self.mod_name)
        self.poseidon_logger.debug(ostr)
        if 'Handle_SectionConfig' in self.actions:
            ostr = '{0}:configure found'.format(self.mod_name)
            self.CONFIG = self.actions['Handle_SectionConfig']
            self.config_section_name = self.mod_name
            for item in self.CONFIG.direct_get(self.config_section_name):
                k, v = item
                self.mod_configuration[k] = v
            ostr = 'mod_name:{0} |mod_configuration: {1}'.format(
                self.mod_name, self.mod_configuration)
            self.poseidon_logger.debug(ostr)
            self.configured = True


class Handle_FullConfig(Monitor_Helper_Base):
    """
    Provides the full configuration file in json dict string
    with sections as keys and their key-value pairs as values.
    """

    def __init__(self):
        super(Handle_FullConfig, self).__init__()
        self.mod_name = self.__class__.__name__
        self.logger = module_logger.logger
        self.poseidon_logger = module_logger.poseidon_logger

    def direct_get(self):
        ''' get the config from the owner '''
        retval = None
        try:
            ret = {}
            for sec in self.owner.config.sections():
                ret[sec] = self.owner.config.items(sec)
            retval = json.dumps(ret)
        except BaseException as e:
            self.logger.error('Failed to open config file because: {0}'.format(str(e)))
            retval = json.dumps('Failed to open config file.')
        return retval


class Handle_SectionConfig(Monitor_Helper_Base):
    """
    Given a section name in the config file,
    returns a json list string of all the key-value
    pairs under that section.
    """

    def __init__(self):
        super(Handle_SectionConfig, self).__init__()
        self.mod_name = self.__class__.__name__

    # direct way
    def direct_get(self, section):
        ''' return the section via the owner '''
        retval = None
        try:
            retval = self.owner.config.items(section)
        except BaseException:
            retval = 'Failed to find section: {0}'.format(section)
        return retval


class Handle_FieldConfig(Monitor_Helper_Base):
    """
    Given a section and corresponding key in the config
    file, returns the value as a string.
    """

    def __init__(self):
        super(Handle_FieldConfig, self).__init__()
        self.logger = module_logger.logger
        self.poseidon_logger = module_logger.poseidon_logger
        self.mod_name = self.__class__.__name__

    def direct_get(self, field, section):
        ''' get the field from the section via owner '''
        ostr = 'Handle_SectionConfig: {0}'.format(section)
        self.logger.debug(ostr)
        retval = ''
        try:
            retval = self.owner.config.get(section, field)
        except BaseException:
            retval = "Can't find field: {0} in section: {1}".format(
                field, section)
        return retval


config_interface = Config()
config_interface.add_endpoint('Handle_SectionConfig', Handle_SectionConfig)
config_interface.add_endpoint('Handle_FieldConfig', Handle_FieldConfig)
config_interface.add_endpoint('Handle_FullConfig', Handle_FullConfig)
