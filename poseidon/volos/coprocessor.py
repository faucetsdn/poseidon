# -*- coding: utf-8 -*-
"""
Created on 30 January 2020
@author: Ryan Ashley
"""
import json
import logging
import os
import subprocess

from pathlib import Path

class Coprocessor(object):

    def __init__(self, controller):
        self.logger = logging.getLogger('coprocessor')
        self.pipette_repo = controller['pipette_repo']
        self.pipette_dir = controller['pipette_dir']
        self.coprocessor_nic = controller['coprocessor_nic']
        self.coprocessor_port = controller['coprocessor_port']
        self.coprocessor_vlans = controller['coprocessor_vlans']
        self.fake_interface = controller['fake_interface']
        self.fake_mac = controller['fake_mac']
        self.fake_server_mac = controller['fake_server_mac']
        self.fake_ips = controller['fake_ips']
        self.bridge = controller['bridge']
        self.pipette_port = controller['pipette_port']
        self.pcap_location = controller['pcap_location']
        self.pcap_size = controller['pcap_size']
        self.pipette_running = False

    def start_coprocessor(self):
        '''
        Starts OVS and containers
        '''
        status = False
        
        return status

    def stop_coprocessor(self):
        '''
        Stops OVS and containers
        '''
        status = False
        
        return status

    