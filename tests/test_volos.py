import logging

from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.volos.acls import VolosAcl
from poseidon_core.volos.coprocessor import Coprocessor
from poseidon_core.volos.volos import Volos

logger = logging.getLogger('test')


class MockLogger:
    def __init__(self):
        self.logger = logger


def test_Volos():
    controller = Config().get_config()
    v = Volos(controller)


def test_Acl():
    controller = Config().get_config()
    endpoint = endpoint_factory('foo')
    endpoint.endpoint_data = {'mac': '00:00:00:00:00:00'}
    a = VolosAcl(endpoint, controller['acl_dir'])


def test_Coprocessor():
    controller = Config().get_config()
    c = Coprocessor(controller)
