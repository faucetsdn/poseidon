#!/usr/bin/env python
#
#   Copyright (c) 2017 In-Q-Tel, Inc, All Rights Reserved.
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
""" Created on 18 September 2017
@author: Jeff Wang
"""
import logging
import logging.handlers
import socket


class Logger:
    """
    Base logger class that handles logging. Outputs to both stderr and a user
    specified syslog. To log, use the class's variable 'logger'
    """
    def __init__(self, name):
        host = 'l0.179.0.101'
        port = 514

        self.count = 0
        self.level_int = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30,
                          'INFO': 20, 'DEBUG' : 10}

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                      '%(module)s:%(lineno)-3d - %(message)s')

        # have it sent to both stderr and a user defined syslog
        sys_err = logging.StreamHandler()
        sys_err.setFormatter(formatter)

        #sys_log = logging.handlers.SysLogHandler(address=(host, port),
        #                                         socktype=socket.SOCK_STREAM)
        #sys_log.setFormatter(formatter)

        self.logger.addHandler(sys_err)
        #self.logger.addHandler(sys_log)
        #sys_log.setFormatter(formatter)

        # logger prints twice if this is not set to false
        self.logger.propagate = False
        
    def set_level(self, level):
        """
        Set the logger level. That level and above gets logged.
        """
        self.logger.setLevel(self.level_int[level.upper()])

    def logger_config(self, config):
        """
        Load configuration files if they exist for loggers.
        """
        if config:
            logging.config.dictConfigClass(config)
        else:
            logging.basicConfig()

    def debug(self, message):
        if self.count % 10 == 0:
            self.logger.debug(message)
            self.count = 1
        else:
            self.count += 1
