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
import logging
import requests
import urllib
import ast
import bson


class Investigator(Main_Action_Base):

    def __init__(self):
        super(Investigator, self).__init__()
        self.mod_name = self.__class__.__name__
        self.logger = self.logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.algos = {}

    def register_algorithm(self, name, algorithm):
        """
        Register investigation algorithm.
        """
        if name not in self.algos:
            self.algos[name] = algorithm
            return True
        return False

    def delete_algorithm(self, name):
        if name in self.algos:
            self.algos.pop(name)
            return True
        return False

    def count_algorithms(self):
        return len(self.algos)
 
    def clear(self):
        self.algos.clear()

    def process_new_machine(self, ip_addr):
        """
        Given the ip of a machine added to the network,
        requests information from the database about the
        ip, then processes accordingly.
        """
        query = {'node_ip': ip_addr}
        query = bson.BSON.encode(query)
        uri = 'http://poseidon-storage-interface/v1/poseidon_records/network_graph/' + query
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
            self.logger.debug('duplicate record for machine: %s', ip_addr)

        def update_config(self):
            pass


investigator_interface = Investigator()
