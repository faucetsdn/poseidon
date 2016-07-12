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
from Action.Action import Action
from Config.Config import FieldConfig
from Config.Config import FullConfig
from Config.Config import SectionConfig
from ControllerPolling.ControllerPolling import ControllerPolling
from falcon_cors import CORS
from NodeHistory.NodeHistory import NodeHistory
from NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import a


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

# make sure to update the yaml file when you add a new route
# routes
api.add_route('/v1/version', VersionResource())
api.add_route('/v1/pcap/{pcap_file}/{output_type}', PCAPResource())

# access to the other components of PoseidonRest
api.add_route('/v1/nbca/{resource}', a.action1())
api.add_route('/v1/polling', ControllerPolling())
api.add_route('/v1/polling', a.action2)

# config routes
api.add_route('/v1/config', FullConfig())
api.add_route('/v1/config/{section}', SectionConfig())
api.add_route('/v1/config/{section}/{field}', FieldConfig())

#api.add_route('/v1/history{resource}', NodeHistory())
api.add_route('/v1/action/{resource}', Action())

# add the functionality for a remote call to trigger scanning
# the internal switch state
#api.add_route('/v1/polling', ControllerPolling())

api.add_route('/swagger.yaml', SwaggerAPI())

print 'done'
