#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import logging.config
import logging.handlers
import os
import socket


class Logger:
    """
    Base logger class that handles logging. Outputs to both stderr and a user
    specified syslog. To log, use the class's variable 'logger'
    """
    host = os.getenv('SYS_LOG_HOST', 'NOT_CONFIGURED')
    port = int(os.getenv('SYS_LOG_PORT', 514))

    level_int = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30,
                 'INFO': 20, 'DEBUG': 10}

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # timestamp - logger_level - class:line number - message
    formatter = logging.Formatter('%(levelname)s - '
                                  '%(module)s:%(lineno)-3d - %(message)s')

    # set the logger to log to stderr
    sys_err = logging.StreamHandler()
    sys_err.setFormatter(formatter)
    logger.addHandler(sys_err)

    # don't try to connect to a syslog address if one was not supplied
    if host != 'NOT_CONFIGURED':  # pragma: no cover
        # if a syslog address was supplied, log to it
        sys_log = logging.handlers.SysLogHandler(
            address=(host, port), socktype=socket.SOCK_STREAM)
        sys_log.setFormatter(formatter)
        logger.addHandler(sys_log)

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
