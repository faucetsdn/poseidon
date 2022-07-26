#!/usr/bin/env python3
# update docker-compose.yaml with release version or dev version, depending on contents of VERSION.
import json
import sys
import urllib.request
from collections import OrderedDict

import ruamel.yaml


# TODO: only updates to Poseidon's main docker-compose.yaml are currently handled.
DOCKER_COMPOSE = "../docker-compose.yaml"
RELEASE_VER = sys.argv[1]
DEV = RELEASE_VER.endswith(".dev")

# These services have their own versions - update automatically.
OWN_VERSIONED_SERVICES = {
    "network_tap": "iqtlabs/network-tools",
}
# For dev versions, add this config.
DEV_SERVICE_OVERRIDE = {
    "poseidon": {"build": {"context": ".", "dockerfile": "Dockerfile"}},
    "poseidon_api": {"build": {"context": "helpers/api", "dockerfile": "Dockerfile"}},
    "rabbit": {"build": {"context": "helpers/rabbitmq", "dockerfile": "Dockerfile"}},
    "workers": {"build": {"context": "workers", "dockerfile": "Dockerfile"}},
}
# For non-dev versions, delete this config.
NON_DEV_SERVICE_DELETE = {
    "poseidon": ["build"],
    "poseidon_api": ["build"],
    "rabbit": ["build"],
    "workers": ["build"],
}

# Broadly preserves formatting.
yaml = ruamel.yaml.YAML()
yaml.indent(mapping=4, sequence=2, offset=4)
dc = ruamel.yaml.round_trip_load(open(DOCKER_COMPOSE).read(), preserve_quotes=True)
for service, service_config in dc["services"].items():
    image, version = service_config["image"].split(":")
    repo = OWN_VERSIONED_SERVICES.get(service, None)
    if repo:
        req = urllib.request.Request(
            url="https://api.github.com/repos/%s/releases/latest" % repo
        )
        res = urllib.request.urlopen(req, timeout=15)  # nosec
        latest_json = json.loads(res.read().decode("utf-8"))
        version = latest_json["name"]
    elif DEV:
        version = "latest"
        if service in DEV_SERVICE_OVERRIDE:
            service_config.update(DEV_SERVICE_OVERRIDE[service])
    else:
        version = "v" + RELEASE_VER
        del_keys = NON_DEV_SERVICE_DELETE.get(service, None)
        if del_keys:
            for del_key in del_keys:
                if del_key in service_config:
                    del service_config[del_key]
    service_config["image"] = ":".join((image, version))


yaml.dump(dc, open(DOCKER_COMPOSE, "w"))
