#!/usr/bin/env python
#
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
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
import logging
import logging.config
from os import environ
from os import getenv
from subprocess import call
from subprocess import check_output

import falcon
from Action.Action import action_interface
from falcon_cors import CORS
from NodeHistory.NodeHistory import nodehistory_interface
from NorthBoundControllerAbstraction.NorthBoundControllerAbstraction import controller_interface

from Config.Config import config_interface


class Monitor(object):

    def __init__(self):
        # get the logger setup
        self.logger = logging.getLogger(__name__)
        self.mod_configuration = dict()
        logging.basicConfig(level=logging.DEBUG)

        self.mod_name = self.__class__.__name__
        self.actions = dict()
        self.Config = config_interface
        self.Config.set_owner(self)
        self.NodeHistory = nodehistory_interface
        self.NodeHistory.set_owner(self)
        self.NorthBoundControllerAbstraction = controller_interface
        self.NorthBoundControllerAbstraction.set_owner(self)
        self.Action = action_interface
        self.Action.set_owner(self)

        # wire up handlers for Config
        print 'handler Config'
        # check
        self.Config.configure()
        self.Config.first_run()
        self.Config.configure_endpoints()

        # wire up handlers for NodeHistory
        print 'handler NodeHistory'
        self.NodeHistory.configure()
        self.NodeHistory.first_run()
        self.NodeHistory.configure_endpoints()

        # wire up handlers for NorthBoundControllerAbstraction
        print 'handler NorthBoundControllerAbstraction'
        # check
        self.NorthBoundControllerAbstraction.configure()
        self.NorthBoundControllerAbstraction.first_run()
        self.NorthBoundControllerAbstraction.configure_endpoints()

        # wire up handlers for Action
        print 'handler Action'
        # check
        self.Action.configure()
        self.Action.first_run()
        self.Action.configure_endpoints()
        print '----------------------'
        self.configSelf()
        self.init_logging()

    def init_logging(self):
        path = getenv('loggingFile', None)

        if path is None:
            path = self.mod_configuration.get('loggingFile', None)

        if path is not None:
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def configSelf(self):
        conf = self.Config.get_endpoint('Handle_SectionConfig')
        for item in conf.direct_get(self.mod_name):
            k, v = item
            self.mod_configuration[k] = v
        print self.mod_name, ':config:', self.mod_configuration

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
poseidon_monitor = Monitor()
poseidon_monitor.add_endpoint('Handle_PCAP', PCAPResource)
poseidon_monitor.add_endpoint('Handle_Yaml', SwaggerAPI)
poseidon_monitor.add_endpoint('Handle_Version', VersionResource)

# make sure to update the yaml file when you add a new route

# 'local' routes
api.add_route('/v1/version', poseidon_monitor.get_endpoint('Handle_Version'))
api.add_route('/v1/pcap/{pcap_file}/{output_type}',
              poseidon_monitor.get_endpoint('Handle_PCAP'))
api.add_route('/swagger.yaml', poseidon_monitor.get_endpoint('Handle_Yaml'))

# access to the other components of PoseidonRest

# nbca routes
api.add_route('/v1/nbca/{resource}',
              poseidon_monitor.NorthBoundControllerAbstraction
              .get_endpoint('Handle_Resource'))
api.add_route('/v1/polling',
              poseidon_monitor.NorthBoundControllerAbstraction
              .get_endpoint('Handle_Periodic'))

# config routes
api.add_route('/v1/config',
              poseidon_monitor.Config.get_endpoint('Handle_FullConfig'))
api.add_route('/v1/config/{section}',
              poseidon_monitor.Config.get_endpoint('Handle_SectionConfig'))
api.add_route('/v1/config/{section}/{field}',
              poseidon_monitor.Config.get_endpoint('Handle_FieldConfig'))

# nodehistory routes
api.add_route('/v1/history/{resource}',
              poseidon_monitor.NodeHistory.get_endpoint('Handle_Default'))

# action routes
api.add_route('/v1/action/{resource}',
              poseidon_monitor.Action.get_endpoint('Handle_Default'))

# storage routes
