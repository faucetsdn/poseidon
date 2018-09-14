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
    Base logger class that handles logging. Outputs to both console, a poseidon
    specific log file and a user specified syslog. To log, use the class's
    variable 'logger'
    """
    host = os.getenv('SYSLOG_HOST', 'NOT_CONFIGURED')
    port = int(os.getenv('SYSLOG_PORT', 514))

    level_int = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30,
                 'INFO': 20, 'DEBUG': 10}

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # logger_level:class:line number - message
    formatter = logging.Formatter('%(levelname)s:'
                                  '%(module)s:%(lineno)-3d - %(message)s')

    # timestamp - logger_level:class:line number - message
    p_formatter = logging.Formatter('%(asctime)s - %(levelname)s:'
                                    '%(module)s:%(lineno)-3d - %(message)s')

    # set the logger to log to console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    poseidon_logger = logging.getLogger('poseidon')
    poseidon_logger.setLevel(logging.INFO)
    poseidon_logger.propagate = False

    # set the poseidon logger to log to file
    try:
        fh = logging.handlers.RotatingFileHandler(
            '/var/log/poseidon.log', backupCount=5, maxBytes=(100*1024*1024))
        fh.setFormatter(p_formatter)
        poseidon_logger.addHandler(fh)
    except Exception as e:
        logger.warning(
            'Unable to setup Poseidon logger because: {0}'.format(str(e)))

    # don't try to connect to a syslog address if one was not supplied
    if host != 'NOT_CONFIGURED':  # pragma: no cover
        # if a syslog address was supplied, log to it
        syslog = logging.handlers.SysLogHandler(
            address=(host, port), socktype=socket.SOCK_STREAM)
        syslog.setFormatter(formatter)
        logger.addHandler(syslog)
        poseidon_logger.addHandler(syslog)

    @staticmethod
    def set_level(level):
        """
        Set the logger level. That level and above gets logged.
        """
        Logger.logger.setLevel(Logger.level_int[level.upper()])
        Logger.poseidon_logger.setLevel(Logger.level_int[level.upper()])

    @staticmethod
    def logger_config(config):
        """
        Load configuration files if they exist for loggers.
        """
        if config:
            logging.config.dictConfigClass(config)
        else:
            logging.basicConfig()
