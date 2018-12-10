# -*- coding: utf-8 -*-
"""
Test module for endpoints.
@author: Charlie Lewis
"""
import os

from poseidon.helpers.endpoint import Endpoint


def test_Endpoint():
    """
    Tests Endpoint
    """
    endpoint = Endpoint('foo')
