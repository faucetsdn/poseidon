
import os
from faucetconfrpc.faucetconfrpc_client_lib import FaucetConfRpcClient
from poseidon.controllers.faucet.helpers import get_config_file, yaml_in, yaml_out


class FaucetConfGetSetter:

    def __init__(self, **_kwargs):
        return

    @staticmethod
    def config_file_path(config_file):
        return config_file


class FaucetLocalConfGetSetter(FaucetConfGetSetter):

    DEFAULT_CONFIG_FILE = None

    def read_faucet_conf(self, config_file):
        if config_file is None:
            config_file = self.DEFAULT_CONFIG_FILE
        config_file = get_config_file(config_file)
        faucet_conf = yaml_in(config_file)
        return faucet_conf

    def write_faucet_conf(self, config_file, faucet_conf):
        if config_file is None:
            config_file = self.DEFAULT_CONFIG_FILE
        config_file = get_config_file(config_file)
        return yaml_out(config_file, faucet_conf)


class FaucetRemoteConfGetSetter(FaucetConfGetSetter):

    def __init__(self, client_key=None, client_cert=None,
                 ca_cert=None, server_addr=None):
        self.client = FaucetConfRpcClient(
            client_key=client_key, client_cert=client_cert,
            ca_cert=ca_cert, server_addr=server_addr)

    @staticmethod
    def config_file_path(config_file):
        if config_file:
            return os.path.basename(config_file)
        return config_file

    def read_faucet_conf(self, config_file):
        return self.client.get_config_file(
            config_filename=self.config_file_path(config_file))

    def write_faucet_conf(self, config_file, faucet_conf):
        return self.client.set_config_file(
            faucet_conf,
            config_filename=self.config_file_path(config_file),
            merge=False)

