import argparse
import os

import bjoern
import falcon
from falcon_cors import CORS

from .routes import routes
from .routes import version


cors = CORS(allow_all_origins=True)
api = application = falcon.App(middleware=[cors.middleware])

r = routes()
for route in r:
    api.add_route(version()+route, r[route])


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port', '-p', help='Port to run the API webserver on', type=int, default=8000)
    parser.add_argument(
        '--prom_addr', '-a', help='Prometheus address connected to Poseidon, i.e. "prometheus:9090"', default='prometheus:9090')
    args = parser.parse_args()

    os.environ['PROM_ADDR'] = args.prom_addr
    bjoern.run(api, '0.0.0.0', args.port)
