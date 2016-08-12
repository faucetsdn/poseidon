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
from poseidon.poseidonMain.Config.Config import config_interface
import logging
import requests
import urllib
import bson
import ast
import sys


class Investigator(Main_Action_Base):

    def __init__(self):
        super(Investigator, self).__init__()
        self.mod_name = self.__class__.__name__
        self.Config = config_interface
        self.set_owner(self)
        self.algos = {}
        self.rules = {}
        self.update_rules()

    def update_config(self):
        """
        Updates configuration based on config file
        (for changing rules).
        """
        self.configure()

    def update_rules(self):
        """
        Updates rules dict from config,
        removes algorithms that are not
        registered.
        """
        self.update_config()
        for key in self.mod_configuration:
            if 'policy' in key:
                self.rules[key] = self.mod_configuration[key].split(' ')

        for policy in self.rules:
            for proposed_algo in self.rules[policy]:
                if proposed_algo not in self.algos:
                    print >> sys.stderr, 'algorithm: %s has not been registered, deleting from policy', proposed_algo
                    del proposed_algo

    def register_algorithm(self, name, algorithm):
        """
        Register investigation algorithm.

        NOTE: for production, replace registering function
        pointers with info about the algorithm (path,
        complexity, etc).
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

    def get_algorithms(self):
        return self.algos

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
            print >> sys.stderr, 'Main (Investigator): could not connect to storage interface'
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
            print >> sys.stderr, 'duplicate record for machine: %s', ip_addr


class Investigator_Response(Investigator):
    """
    Investigator_Response manages and tracks the
    system response to an event (ie new machine
    added to network, etc). Maintains a record of
    jobs scheduled
    """
    def __init__(self, address):
        super(Investigator_Response, self).__init__()
        self.address = address

    def vent_preparation(self):
        """
        Prepares vent jobs based on algorithms
        available to be used and investigator
        rules.
        """
        try:
            resp = requests.get('contact vent to get instances running')
        except:
            print >> sys.stderr, 'Main: Investigator: vent_preparation, vent request failed'

    def send_vent_jobs(self):
        """
        Connects to vent and sends prepared
        jobs for analysis, waits for results
        and then continues with appropriate
        response.
        """
        try:
            resp = requests.get('vent_url')
        except:
            print >> sys.stderr, 'Main: Investigator: send_vent_jobs, vent request failed'

    def update_record(self):
        """
        Update database based on processing
        results and update network posture.
        """
        try:
            url = 'http://poseidon-storage-interface/v1/'
            resp = requests.get(url)
        except:
            pass


investigator_interface = Investigator()
