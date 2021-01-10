from poseidon_core.helpers.config import Config


class Mirror:

    def __init__(self, logger):
        config = Config().get_config()
        self.mirror_ports = config['MIRROR_PORTS']
        self.proxy_mirror_ports = config['controller_proxy_mirror_ports']
        self.tunnel_vlan = config['tunnel_vlan']
        self.tunnel_name = config['tunnel_name']
        self.ignore_vlans = config['ignore_vlans']
        self.ignore_ports = config['ignore_ports']
        self.trunk_ports = config['truck_ports']

    def mirror_port(self, switch, port):
        self.logger.warning(f'Unable to mirror {switch}:{port}')
        return False

    def unmirror_port(self, switch, port):
        self.logger.warning(f'Unable to unmirror {switch}:{port}')
        return False

    def mirror_mac(self, switch, port, mac):
        self.logger.warning(f'Unable to mirror {switch}:{port}:{mac}')
        return False

    def unmirror_mac(self, switch, port, mac):
        self.logger.warning(f'Unable to unmirror {switch}:{port}:{mac}')
        return False

    def mirror_endpoint(self, endpoint):
        self.logger.warning(f'Unable to mirror {endpoint.name}')
        return False

    def unmirror_endpoint(self, endpoint):
        self.logger.warning(f'Unable to unmirror {endpoint.name}')
        return False

    def clear_mirrors(self):
        self.logger.warning('Unable to clear all mirrors')
        return False
