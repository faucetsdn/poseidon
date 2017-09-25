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
    host = 'localhost'
    port = 514

    level_int = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30,
                      'INFO': 20, 'DEBUG' : 10}

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                  '%(module)s:%(lineno)-3d - %(message)s')

    # have it sent to both stderr and a user defined syslog
    sys_err = logging.StreamHandler()
    sys_err.setFormatter(formatter)

    # type in the address explicitly . Python doesn't like it if the host is
    # in variable form
    sys_log = logging.handlers.SysLogHandler(address=('10.179.0.101', port),
                                             socktype=socket.SOCK_STREAM)
    sys_log.setFormatter(formatter)

    logger.addHandler(sys_err)
    logger.addHandler(sys_log)
    sys_log.setFormatter(formatter)

    # logger prints twice if this is not set to false
    logger.propagate = False

    @staticmethod
    def set_level(level):
        """
        Set the logger level. That level and above gets logged.
        """
        Logger.logger.setLevel(Logger.level_int[level.upper()])

    @staticmethod
    def logger_config(config):
        """
        Load configuration files if they exist for loggers.
        """
        if config:
            logging.config.dictConfigClass(config)
        else:
            logging.basicConfig()
