#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
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
""" Created on  18 July 2016
@author: dgrossman
"""
from Logger_Base import Logger

module_logger = Logger.logger


class Rock_Bottom(object):
    """Bottom most poseidon class

    Attributes:
        configured (boolean): True when class configuration is valid
        config_section_name (str): section key for this class
        upper level names are concatenated before lower level names

        mod_name (str): name of this module
        mod_configuration (dict): key value store of config items
        owner (class) : instantiated class holding this class

    """

    def __init__(self):
        self.configured = False
        self.config_section_name = None
        self.mod_name = self.__class__.__name__
        self.mod_configuration = None
        self.owner = None
        self.logger = None
