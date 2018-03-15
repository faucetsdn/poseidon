def routes():
    from .data import Endpoints, Info, Network
    endpoints = Endpoints()
    p = paths()
    info = Info()
    network = Network()
    funcs = [endpoints, info, network]
    return dict(zip(p, funcs))

def paths():
    return ['', '/info', '/network']

def version():
    return '/v1'
