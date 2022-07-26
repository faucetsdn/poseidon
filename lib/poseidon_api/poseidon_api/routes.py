def routes():
    from .data import Endpoints, Info, Network, NetworkByIp, NetworkFull
    endpoints = Endpoints()
    p = paths()
    info = Info()
    network = Network()
    network_by_ip = NetworkByIp()
    network_full = NetworkFull()
    funcs = [endpoints, info, network, network_by_ip, network_full]
    return dict(zip(p, funcs))


def paths():
    return ['', '/info', '/network', '/network/{ip}', '/network_full']


def version():
    return '/v1'
