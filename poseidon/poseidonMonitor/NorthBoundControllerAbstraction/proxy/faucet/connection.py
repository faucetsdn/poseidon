#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2016-2017 In-Q-Tel, Inc, All Rights Reserved.
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
Created on 18 November 2017
@author: cglewis
"""
from paramiko import AutoAddPolicy, SSHClient
from scp import SCPClient

from poseidon.baseClasses.Logger_Base import Logger

module_logger = Logger.logger


class Connection:

    def __init__(self, host, user=None, pw=None, *args, **kwargs):
        self.logger = module_logger
        self.host = host
        self.user = user
        self.pw = pw

    def connect(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.connect(self.host, username=self.user, password=self.pw)
        self.ssh = ssh

    def close_connection(self):
        if self.ssh:
            self.ssh.close()

    def exec_command(self, command):
        pass

    def receive_file(self, file_path):
        pass

    def send_file(self, file_path):
        pass
