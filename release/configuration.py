#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration script to update makefile and other build process files
with necessary version and configuration info

Created on 17 June 2019
@author: Ryan Ashley
"""

'''
cmd_str += "docker pull {0}/{1}:{2}\n"
                cmd_str += "docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/{0}-{1}.tar {0}/{1}:{2}\n".format(owner, tool, branch)
'''

import argparse
import json
from sys import exit
from string import Template
import os
import yaml

def parse_cfg_from_yml(yml_dict):
    cfg_dict ={}
    for key in yml_dict.keys():
        repo_slash_idx = key.rfind('/')
        owner_slash_idx = key.rfind('/', 0, repo_slash_idx-1)
        if owner_slash_idx > 0 and repo_slash_idx > 0:
            owner = key[owner_slash_idx+1:repo_slash_idx]
            repo = key[repo_slash_idx+1:]
            for sub_key in yml_dict[key].keys():
                branch = yml_dict[key][sub_key]["branch"]
                tool = repo + "-" + sub_key.replace("_", "-") if sub_key != "@" else repo

                # take the version of the 
                if repo == "vent" and not "vent" in cfg_dict:
                    cfg_dict["vent"] = {'owner': owner, 'repo': 'vent', 'version': branch}

                cfg_dict[tool] = {'owner': owner, 'repo': repo, 'version': branch}

                

    return cfg_dict

def generate_makefile(cfg_dict):
    vent = cfg_dict["vent"]
    vent_cmd = "docker pull {0}/{1}:{2}\n\t".format(vent["owner"], "vent", vent["version"])
    vent_cmd += "docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/{0}-{1}.tar {0}/{1}:{2}\n\t".format(vent["owner"], "vent", vent["version"])

    tool_cmd = ""
    for key in list(cfg_dict.keys())[1:]:
        value = cfg_dict[key]
        tool_cmd += "docker pull {0}/{1}:{2}\n\t".format(value["owner"], key, value["version"])
        tool_cmd += "docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/{0}-{1}.tar {0}/{1}:{2}\n\t".format(value["owner"], key, value["version"])
    cmds = vent_cmd + tool_cmd
    with open("./release/templates/make", "r") as tf:
        temp_str = tf.read()
        template = Template(temp_str)
        replaced = template.substitute(VENT_COMMAND=vent_cmd, TOOL_COMMANDS=tool_cmd)

    with open("Makefile", "w") as rf:
        rf.write(replaced)

def generate_deb_postinst(cfg_dict):
    tool_cmd = ""
    for key in cfg_dict.keys():
        value = cfg_dict[key]
        tool_cmd += "    if [ ! -f /opt/poseidon/dist/{0}-{1}.tar ]; then\n".format(value["owner"], key)
        tool_cmd += "        docker pull {0}/{1}:{2}\n".format(value["owner"], key, value["version"])
        tool_cmd += "    else\n"
        tool_cmd += "        docker load -i /opt/poseidon/dist/{0}-{1}.tar\n".format(value["owner"], key)
        tool_cmd += "    fi\n"

    with open("./release/templates/deb_postinst", "r") as dp:
        temp_str = dp.read()
        template = Template(temp_str)
        replaced = template.substitute(LOAD_OR_PULL_COMMANDS=tool_cmd)

    with open("installers/debian/postinst", "w") as rf:
        rf.write(replaced)

def generate_deb_control(poseidon_version):
    with open("./release/templates/deb_control", "r") as dc:
        temp_str = dc.read()
        template = Template(temp_str)
        replaced = template.substitute(POSEIDON_VERSION=poseidon_version)

    with open("installers/debian/control", "w") as rf:
        rf.write(replaced)

def generate_version_file(poseidon_version):
    with open("VERSION", "w") as v:
        v.write("{0}".format(poseidon_version))

def generate_readme(poseidon_version):
    with open("./release/templates/readme", "r") as rm:
        temp_str = rm.read()
        template = Template(temp_str)
        replaced = template.substitute(POSEIDON_VERSION=poseidon_version)

    with open("README.md", "w") as rf:
        rf.write(replaced)

def generate_bin_poseidon(vent_data):
    vent_slug = "{0}/{1}:{2}".format(vent_data["owner"], "vent", vent_data["version"])
    with open("./release/templates/bin_poseidon", "r") as bp:
        temp_str = bp.read()
        template = Template(temp_str)
        replaced = template.substitute(VENT_SLUG=vent_slug)

    with open("bin/poseidon", "w") as rf:
        rf.write(replaced)

def main(startup_file):
    if os.path.exists(startup_file):
        # rewrite the yml file to exclusively lowercase
        with open(startup_file, 'r') as sup:
            vent_startup = sup.read()
        with open(startup_file, 'w') as sup:
            for line in vent_startup:
                sup.write(line.lower())
        with open(startup_file, 'r') as sup:
            yml_dict = yaml.safe_load(sup.read())

        if not yml_dict :
            print("configuration could not be loaded from {0}. exiting...".format(startup_file))
            exit(1)

        cfg = parse_cfg_from_yml(yml_dict)
        if not cfg:
            print("configuration could not be parsed from yml supplied by {0}. exiting...".format(startup_file))
            exit(1)

        poseidon_version = cfg["poseidon"]["version"][1:]
        vent_version = cfg["vent"]["version"]

        print("Generating release files for Poseion version: {0}".format(poseidon_version))
        print("Using Vent version: {0}".format(vent_version))

        print("Generating Makefile")
        generate_makefile(cfg)
        print("Generating debian/postinst")
        generate_deb_postinst(cfg)

        print("Generating debian/control")
        generate_deb_control(poseidon_version)
        print("Generating bin/poseidon")
        generate_bin_poseidon(cfg["vent"])
        print("Populating VERSION file")
        generate_version_file(poseidon_version)
        print("Generating README.md")
        generate_readme(poseidon_version)
        print("Complete")
        print("Release files successfully generated!")
        


if __name__ == '__main__':  # pragma: no cover
    main(startup_file=".vent_startup.yml")