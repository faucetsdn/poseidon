# -*- coding: utf-8 -*-
"""
Created on 4 March 2020
@author: Charlie Lewis
"""
import os
import tempfile

import yaml

from poseidon_core.helpers.exception_decor import exception


def represent_none(dumper, _):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')


@exception
def get_config_file(config_file):
    # TODO check for other files
    if not config_file:
        # default to FAUCET default
        config_file = '/etc/faucet/faucet.yaml'
    return config_file


def parse_rules(config_file):
    config_file = get_config_file(config_file)
    obj_doc = yaml_in(config_file)
    return obj_doc


@exception
def yaml_in(config_file):
    try:
        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except Exception as e:  # pragma: no cover
        return False


@exception
def yaml_out(config_file, obj_doc):
    stream = tempfile.NamedTemporaryFile(
        prefix=os.path.basename(config_file),
        dir=os.path.dirname(config_file),
        mode='w',
        delete=False)
    yaml.add_representer(type(None), represent_none)
    yaml.dump(obj_doc, stream, default_flow_style=False)
    stream.close()
    os.replace(stream.name, config_file)
    return True
