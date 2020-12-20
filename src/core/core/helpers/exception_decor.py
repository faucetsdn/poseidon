# -*- coding: utf-8 -*-
"""
Created on 27 December 2018
@author: Charlie Lewis
"""
import functools
import logging


def exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('exception')
        try:
            return function(*args, **kwargs)
        except Exception as e:
            # log the exception
            logger.exception('Exception in {0}: {1}'.format(
                function.__name__, str(e)))
            return False
    return wrapper
