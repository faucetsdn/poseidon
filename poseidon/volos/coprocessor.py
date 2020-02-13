# -*- coding: utf-8 -*-
"""
Created on 30 January 2020
@author: Ryan Ashley
"""
import git
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
        self.coprocessor_vlan = controller['coprocessor_vlan']
        self.fake_interface = controller['fake_interface']
        self.fake_mac = controller['fake_mac']
        self.fake_server_mac = controller['fake_server_mac']
        self.fake_ip = controller['fake_ip']
        self.bridge = controller['bridge']
        self.pipette_port = controller['pipette_port']
        self.pcap_location = controller['pcap_location']
        self.pcap_size = controller['pcap_size']
        self.pipette_running = False

    def update_pipette(self):
        status = True
        try:
            if not os.path.exists(self.pipette_dir):
                Path(self.pipette_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:  # pragma: no cover
            self.logger.error('Pipette directory:{0} could not be created. Coprocessing may not work as expected. {1}'
                .format(self.pipette_dir, str(e)))
            status = False
        if status :
            try:
                repo = git.Repo(self.pipette_dir)
            except git.exc.InvalidGitRepositoryError: # pragma: no cover
                repo = git.Repo.clone_from(self.pipette_repo, self.pipette_dir)
            if repo and not repo.bare :
                repo.remotes.origin.pull()

        return status
    def start_pipette(self):
        '''
        pipette params:
        -c,  coproint      interface to send coprocessed traffic to
        -f,  fakeint       interface created for fake services to run on
        -m,  fakemac       fake mac for fake interface
        -fch, fakeclientmac fake client mac address
        -i,  fakeip        fake ip for fake services(will be proxied from real IPS)
        -b,  bridge        name of ovs bridge to create
        -p,  port          pipette port
        -r,  record
        '''
        pipette_script = os.path.join(self.pipette_dir, "runpipette.sh")
        params = [
            pipette_script,
            f"-c {self.coprocessor_nic}",
            f"-f {self.fake_interface}",
            f"-m {self.fake_mac}",
            f"-fch {self.fake_server_mac}",
            f"-i {self.fake_ip}",
            f"-b {self.bridge}",
            f"-p {self.pipette_port}",
            f"-r {self.pcap_location} {self.pcap_size}",
            ]
        process = subprocess.Popen(params, 
                           #stdout=subprocess.PIPE,
                           #stderr=subprocess.PIPE,
                           universal_newlines=True)

    def stop_pipette(self):
        '''
        pipette params:
        -c,  coproint      interface to send coprocessed traffic to
        -f,  fakeint       interface created for fake services to run on
        -b,  bridge        name of ovs bridge to create"
        '''
        pipette_script = os.path.join(self.pipette_dir, "shutdownpipette.sh")
        params = [
            pipette_script,
            f"-c {self.coprocessor_nic}",
            f"-f {self.fake_interface}",
            f"-b {self.bridge}",
            ]
        process = subprocess.Popen(params, 
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)

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

    