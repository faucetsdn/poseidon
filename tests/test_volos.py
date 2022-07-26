from poseidon_core.helpers.config import Config
from poseidon_core.helpers.endpoint import endpoint_factory
from poseidon_core.operations.primitives.coprocess import Coprocess
from poseidon_core.operations.volos.acls import VolosAcl
from poseidon_core.operations.volos.volos import Volos


def test_Volos():
    controller = Config().get_config()
    v = Volos(controller)


def test_Acl():
    controller = Config().get_config()
    endpoint = endpoint_factory("foo")
    endpoint.endpoint_data = {"mac": "00:00:00:00:00:00"}
    a = VolosAcl(endpoint, controller["acl_dir"])


def test_Coprocess():
    controller = Config().get_config()
    c = Coprocess(controller)
