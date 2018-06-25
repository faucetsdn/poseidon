from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump

app = Flask(__name__)

health = HealthCheck(app, "/healthcheck")
envdump = EnvironmentDump(app, "/environment")


def application_data():
    return {"maintainer": "Charlie Lewis",
            "git_repo": "https://github.com/CyberReboot/poseidon",
            "app": "poseidon"}

envdump.add_section("application", application_data)
