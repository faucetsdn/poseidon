# -*- coding: utf-8 -*-
"""
Created on 25 Oct 2017
@author: dgrossman
"""
from poseidon.helpers.log import Logger


def test_logger_base():
    class MockLogger(Logger):
        def __init__(self):
            pass

    logger = MockLogger()
    logger.logger_config(None)
