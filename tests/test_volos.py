import os
import json
import logging

from poseidon.helpers.config import Config
from poseidon.volos.volos import Volos

logger = logging.getLogger('test')

class MockLogger:
    def __init__(self):
        self.logger = logger

def test_Volos():
	controller = Config().get_config()
	v = Volos(controller)