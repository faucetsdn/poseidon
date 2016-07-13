#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This example is a test of a usable API demonstrating the test and documentation
workflow for the code base.

Created on 17 May 2016
@author: Charlie Lewis, dgrossman
"""
import json
from os import environ
from subprocess import call
from subprocess import check_output

import falcon
from Action.Action import action_interface
from Config.Config import config_interface
from falcon_cors import CORS
from NodeHistory.NodeHistory import nodehistory_interface
from NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import controller_interface


class Register(object):

    def __init__(self):
        self.mod_name = self.__class__.__name__
        self.actions = dict()
        self.Config = config_interface
        self.Config.owner = self
        self.NodeHistory = nodehistory_interface
        self.NodeHistory.owner = self
        self.NorthBoundControllerAbstraction = controller_interface
        self.NorthBoundControllerAbstraction.owner = self
        self.Action = action_interface
        self.Action.owner = self

        # wire up handlers for Config

        # wire up handlers for NodeHistory

        # wire up handlers for NorthBoundControllerAbstraction

        # wire up handlers for Action

    def add_endpoint(self, name, handler):
        a = handler()
        a.owner = self
        self.actions[name] = a

    def del_endpoint(self, name):
        if name in self.actions:
            self.actions.pop(name)

    def get_endpoint(self, name):
        if name in self.actions:
            return self.actions.get(name)
        else:
            return None


def get_allowed():
    rest_url = 'localhost:8555'
    if 'ALLOW_ORIGIN' in environ:
        allow_origin = environ['ALLOW_ORIGIN']
        host_port = allow_origin.split('//')[1]
        host = host_port.split(':')[0]
        port = str(int(host_port.split(':')[1]))
        rest_url = host + ':' + port
    else:
        allow_origin = ''
    return allow_origin, rest_url

allow_origin, rest_url = get_allowed()
cors = CORS(allow_origins_list=[allow_origin])
public_cors = CORS(allow_all_origins=True)


class SwaggerAPI:
    """Serve up swagger API"""
    swagger_file = 'poseidon/poseidonMonitor/swagger.yaml'

    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.content_type = 'text/yaml'
        try:
            # update mydomain with current running host and port
            with open(self.swagger_file, 'r') as f:
                filedata = f.read()
            newdata = filedata.replace('mydomain', rest_url)
            with open(self.swagger_file, 'w') as f:
                f.write(newdata)

            with open(self.swagger_file, 'r') as f:
                resp.body = f.read()
        except:  # pragma: no cover
            resp.body = ''


class VersionResource:
    """Serve up the current version and build information"""
    version_file = 'VERSION'

    def on_get(self, req, resp):
        """Handles GET requests"""
        version = {}
        # get version number (from VERSION file)
        try:
            with open(self.version_file, 'r') as f:
                version['version'] = f.read().strip()
        except:  # pragma: no cover
            pass
        # get commit id (git commit ID)
        try:
            cmd = 'git -C poseidon rev-parse HEAD'
            commit_id = check_output(cmd, shell=True)
            cmd = 'git -C poseidon diff-index --quiet HEAD --'
            dirty = call(cmd, shell=True)
            if dirty != 0:
                version['commit'] = commit_id.strip() + '-dirty'
            else:
                version['commit'] = commit_id.strip()
        except:  # pragma: no cover
            pass
        # get runtime id (docker container ID)
        try:
            if 'HOSTNAME' in environ:
                version['runtime'] = environ['HOSTNAME']
        except:  # pragma: no cover
            pass
        resp.body = json.dumps(version)


class PCAPResource:
    """Serve up parsed PCAP files"""

    def on_get(self, req, resp, pcap_file, output_type):
        resp.content_type = 'text/text'
        try:
            if output_type == 'pcap' and pcap_file.split('.')[1] == 'pcap':
                resp.body = check_output(
                    ['/usr/sbin/tcpdump',
                     '-r',
                     '/tmp/' + pcap_file,
                     '-ne',
                     '-tttt'])
            else:
                resp.body = 'not a pcap'
        except:  # pragma: no cover
            resp.body = 'failed'


# create callable WSGI app instance for gunicorn
api = falcon.API(middleware=[cors.middleware])

# register the local classes
register = Register()
register.add_endpoint('Handle_PCAP', PCAPResource)
register.add_endpoint('Handle_Yaml', SwaggerAPI)
register.add_endpoint('Handle_Version', VersionResource)

# make sure to update the yaml file when you add a new route

# 'local' routes
api.add_route('/v1/version', register.get_endpoint('Handle_Version'))
api.add_route('/v1/pcap/{pcap_file}/{output_type}',
              register.get_endpoint('Handle_PCAP'))
api.add_route('/swagger.yaml', register.get_endpoint('Handle_Yaml'))

# access to the other components of PoseidonRest

# nbca routes
api.add_route('/v1/nbca/{resource}',
              register.NorthBoundControllerAbstraction
              .get_endpoint('Handle_Resource'))
api.add_route('/v1/polling',
              register.NorthBoundControllerAbstraction
              .get_endpoint('Handle_Periodic'))

# config routes
api.add_route('/v1/config',
              register.Config.get_endpoint('Handle_FullConfig'))
api.add_route('/v1/config/{section}',
              register.Config.get_endpoint('Handle_SectionConfig'))
api.add_route('/v1/config/{section}/{field}',
              register.Config.get_endpoint('Handle_FieldConfig'))

# nodehistory routes
api.add_route('/v1/history/{resource}',
              register.NodeHistory.get_endpoint('Handle_Default'))

# action routes
api.add_route('/v1/action/{resource}',
              register.Action.get_endpoint('Handle_Default'))

# storage routes
