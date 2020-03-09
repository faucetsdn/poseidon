# -*- coding: utf-8 -*-
"""
Created on 19 November 2017
@author: Charlie Lewis
"""
import yaml

from poseidon.helpers.exception_decor import exception


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
        stream = open(config_file, 'r')
        obj_doc = yaml.safe_load(stream)
        stream.close()
    except Exception as e:  # pragma: no cover
        return False
    return obj_doc


@exception
def yaml_out(config_file, obj_doc):
    stream = open(config_file, 'w')
    yaml.add_representer(type(None), represent_none)
    yaml.dump(obj_doc, stream, default_flow_style=False)
    return True
