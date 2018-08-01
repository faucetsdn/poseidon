def routes():
    from .data import Endpoints, Info, Network, NetworkFull
    endpoints = Endpoints()
    p = paths()
    info = Info()
    network = Network()
    network_full = NetworkFull()
    funcs = [endpoints, info, network, network_full]
    return dict(zip(p, funcs))


def paths():
    return ['', '/info', '/network', '/network_full']


def version():
    return '/v1'
