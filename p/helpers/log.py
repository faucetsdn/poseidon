# -*- coding: utf-8 -*-
""" Created on 18 September 2017
@author: Jeff Wang
"""
import logging
import logging.handlers
import os
import socket

from p.helpers.config import Config


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

    controller = Config().set_config()

    # logger_level:class:line number - message
    formatter = logging.Formatter('%(levelname)s:'
                                  '%(module)s:%(lineno)-3d - %(message)s')

    # timestamp - logger_level:class:line number - message
    p_formatter = logging.Formatter('%(asctime)s - %(levelname)s:'
                                    '%(module)s:%(lineno)-3d - %(message)s')

    log_format = '[%(levelname)s] %(name)s - %(message)s'
    logging.basicConfig(
        level=level_int[controller['logger_level'].upper()], format=log_format)

    poseidon_logger = logging.getLogger('poseidon')
    logger = logging.getLogger('console')

    logger.setLevel(level_int[controller['logger_level'].upper()])
    poseidon_logger.setLevel(level_int[controller['logger_level'].upper()])

    # set the logger to log to console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    use_file_logger = True
    # ensure log file exists
    try:
        if not os.path.exists('/var/log/poseidon'):
            os.makedirs('/var/log/poseidon')
        if not os.path.exists('/var/log/poseidon/poseidon.log'):
            with open('/var/log/poseidon/poseidon.log', 'w'):
                pass
    except Exception as e:
        use_file_logger = False
        logger.warning(
            'Unable to setup Poseidon logger because: {0}'.format(str(e)))

    if use_file_logger:
        # set the poseidon logger to log to file
        try:
            fh = logging.handlers.RotatingFileHandler(
                '/var/log/poseidon/poseidon.log')
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
