from flask import Flask

from healthcheck import EnvironmentDump
from healthcheck import HealthCheck

app = Flask(__name__)

health = HealthCheck(app, '/healthcheck')
envdump = EnvironmentDump(app, '/environment')


def application_data():
    return {'maintainer': 'Charlie Lewis',
            'app': 'packet_cafe_worker'}


envdump.add_section('application', application_data)
