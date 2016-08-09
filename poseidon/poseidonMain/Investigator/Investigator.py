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
Module for applying user-defined rules to
network flows.

Created on 17 May 2016
@author: dgrossman, tlanham
"""
from poseidon.baseClasses.Main_Action_Base import Main_Action_Base
import requests
import urllib
import ast


class Investigator(Main_Action_Base):

    def __init__(self):
        super(Investigator, self).__init__()
        self.mod_name = self.__class__.__name__
        self.algos = {}

    def register_algorithm(self, name, algorithm):
        """
        Register investigation algorithm.
        """
        self.algos[name] = algorithm

    def process_new_machine(self, ip_addr):
        """
        Given the ip of a machine added to the network,
        requests information from the database about the
        ip, then processes accordingly.
        """
        query = {'node_ip': ip_addr}
        uri = 'http://poseidon-storage-interface/v1/poseidon_records/network_graph/' + str(query)
        uri = urllib.unquote(str(query)).encode('utf8')
        try:
            resp = requests.get(uri)
        except:
            # error connecting to storage interface
            # log error
            return

        resp = ast.literal_eval(resp.body)
        if resp['count'] <= 0:
            # machine has no info in db or error on query
            pass
        elif resp['count'] == 1:
            # there is a record for machine
            info = resp['body']
        else:
            # bad - should only be one record for each ip
            # log error for investigation
            logger = self.logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)

        def update_config(self):
            pass

investigator_interface = Investigator()
