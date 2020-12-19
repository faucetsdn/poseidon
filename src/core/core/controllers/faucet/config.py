import logging
import os
import sys

import yaml
from faucetconfrpc.faucetconfrpc_client_lib import FaucetConfRpcClient

from poseidon_core.controllers.faucet.helpers import get_config_file
from poseidon_core.controllers.faucet.helpers import yaml_in
from poseidon_core.controllers.faucet.helpers import yaml_out


class FaucetConfGetSetter:

    DEFAULT_CONFIG_FILE = ''

    def __init__(self, **_kwargs):
        self.faucet_conf = {}

    def read_faucet_conf(self, config_file):
        # TODO dummy function for set_acls
        return

    def write_faucet_conf(self, config_file):
        # TODO dummy function for set_acls
        return

    @staticmethod
    def config_file_path(config_file):
        return config_file

    def set_acls(self, acls):
        self.read_faucet_conf(config_file=None)
        self.faucet_conf['acls'] = acls
        self.write_faucet_conf(config_file=None)

    def get_dps(self):  # pragma: no cover
        raise NotImplementedError

    def get_switch_conf(self, dp):
        return self.get_dps().get(dp, None)

    def get_port_conf(self, dp, port):
        switch_conf = self.get_switch_conf(dp)
        if not switch_conf:
            return None
        return switch_conf['interfaces'].get(port, None)

    def get_stack_root_switch(self):
        root_stack_switch = [
            switch for switch, switch_conf in self.get_dps().items()
            if switch_conf.get('stack', {}).get('priority', None)]
        if root_stack_switch:
            return root_stack_switch[0]
        return None

    def set_port_conf(self, dp, port, port_conf):  # pragma: no cover
        raise NotImplementedError

    def update_switch_conf(self, dp, switch_conf):  # pragma: no cover
        raise NotImplementedError

    def mirror_port(self, dp, mirror_port, port):  # pragma: no cover
        raise NotImplementedError

    def unmirror_port(self, dp, mirror_port, port):  # pragma: no cover
        raise NotImplementedError

    def clear_mirror_port(self, dp, mirror_port):  # pragma: no cover
        raise NotImplementedError


class FaucetLocalConfGetSetter(FaucetConfGetSetter):

    def read_faucet_conf(self, config_file):
        if not config_file:
            config_file = self.DEFAULT_CONFIG_FILE
        config_file = get_config_file(config_file)
        faucet_conf = yaml_in(config_file)
        if faucet_conf is None:
            logging.error('Faucet config is empty, exiting.')
            sys.exit(1)
        if isinstance(faucet_conf, dict):
            self.faucet_conf = faucet_conf
        return self.faucet_conf

    def write_faucet_conf(self, config_file=None, faucet_conf=None):
        if not config_file:
            config_file = self.DEFAULT_CONFIG_FILE
        if faucet_conf is None:
            faucet_conf = self.faucet_conf
        self.faucet_conf = faucet_conf
        config_file = get_config_file(config_file)
        return yaml_out(config_file, self.faucet_conf)

    def get_dps(self):
        self.read_faucet_conf(config_file=None)
        return self.faucet_conf.get('dps', {})

    def set_port_conf(self, dp, port, port_conf):
        switch_conf = self.get_switch_conf(dp)
        if not switch_conf:
            return None
        switch_conf['interfaces'][port] = port_conf
        self.write_faucet_conf()

    def update_switch_conf(self, dp, switch_conf):
        self.faucet_conf['dps'][dp].update(switch_conf)
        self.write_faucet_conf()

    def _get_mirrored_ports(self, dp, mirror_port):
        mirror_interface_conf = self.get_port_conf(dp, mirror_port)
        mirrored_ports = None
        if mirror_interface_conf:
            mirrored_ports = mirror_interface_conf.get('mirror', None)
        return mirror_interface_conf, mirrored_ports

    def _set_mirror_config(self, dp, mirror_port, mirror_interface_conf, ports=None):
        if ports:
            if isinstance(ports, set):
                ports = list(ports)
            if not isinstance(ports, list):
                ports = [ports]
            mirror_interface_conf['mirror'] = ports
        # Don't delete DP level config when setting mirror list to empty,
        # as that could cause an unnecessary cold start.
        elif 'mirror' in mirror_interface_conf:
            del mirror_interface_conf['mirror']
        self.set_port_conf(dp, mirror_port, mirror_interface_conf)

    def mirror_port(self, dp, mirror_port, port):
        mirror_interface_conf, ports = self._get_mirrored_ports(
            dp, mirror_port)
        if ports is None:
            ports = []
        ports = set(ports)
        ports.add(port)
        self._set_mirror_config(dp, mirror_port, mirror_interface_conf, ports)

    def unmirror_port(self, dp, mirror_port, port):
        mirror_interface_conf, ports = self._get_mirrored_ports(
            dp, mirror_port)
        if ports is None:
            ports = []
        ports = set(ports)
        if port in ports:
            ports.remove(port)
            self._set_mirror_config(
                dp, mirror_port, mirror_interface_conf, ports)

    def clear_mirror_port(self, dp, mirror_port):
        mirror_interface_conf, _ = self._get_mirrored_ports(dp, mirror_port)
        self._set_mirror_config(dp, mirror_port, mirror_interface_conf)


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
        self.faucet_conf = self.client.get_config_file(
            config_filename=self.config_file_path(config_file))
        if self.faucet_conf is None:
            logging.error('Faucet config is empty, exiting.')
            sys.exit(1)
        return self.faucet_conf

    def write_faucet_conf(self, config_file=None, faucet_conf=None, merge=False):
        if not config_file:
            config_file = self.DEFAULT_CONFIG_FILE
        if faucet_conf is None:
            faucet_conf = self.faucet_conf
        return self.client.set_config_file(
            self.faucet_conf,
            config_filename=self.config_file_path(config_file),
            merge=merge)

    def get_dps(self):
        self.read_faucet_conf(config_file=None)
        return self.faucet_conf.get('dps', {})

    def set_port_conf(self, dp, port, port_conf):
        return self.client.set_dp_interfaces(
            [(dp, {port: yaml.dump(port_conf)})])

    def update_switch_conf(self, dp, switch_conf):
        return self.write_faucet_conf(
            faucet_conf={'dps': {dp: switch_conf}}, merge=True)

    def mirror_port(self, dp, mirror_port, port):  # pragma: no cover
        self.client.add_port_mirror(dp, port, mirror_port)

    def unmirror_port(self, dp, mirror_port, port):  # pragma: no cover
        self.client.remove_port_mirror(dp, port, mirror_port)

    def clear_mirror_port(self, dp, mirror_port):  # pragma: no cover
        self.client.clear_port_mirror(dp, mirror_port)
