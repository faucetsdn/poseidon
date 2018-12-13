# -*- coding: utf-8 -*-
"""
Created on 18 November 2017
@author: Charlie Lewis
"""
import logging
import os

from paramiko import AutoAddPolicy
from paramiko import SSHClient
from scp import SCPClient


class Connection:

    def __init__(self,
                 host=None,
                 user=None,
                 pw=None,
                 config_file=None,
                 log_file=None,
                 *args,
                 **kwargs):
        self.logger = logging.getLogger('connection')
        self.host = host
        self.user = user
        self.pw = pw
        self.config_file = config_file
        self.log_file = log_file
        self.ssh = None
        if self.host:
            # ensure directories exist
            self.config_dir = '/etc/faucet'
            self.log_dir = '/var/log/faucet'
            try:
                if not os.path.exists(self.config_dir):
                    os.makedirs(self.config_dir)
            except PermissionError:
                self.config_dir = os.path.join(os.getcwd(), 'faucet')
                if not os.path.exists(self.config_dir):
                    os.makedirs(self.config_dir)
            try:
                if not os.path.exists(self.log_dir):
                    os.makedirs(self.log_dir)
            except PermissionError:
                self.log_dir = os.path.join(os.getcwd(), 'faucet')
                if not os.path.exists(self.log_dir):
                    os.makedirs(self.log_dir)

    def _connect(self):
        # TODO better logging
        try:
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.user, password=self.pw,
                        timeout=10, auth_timeout=10, banner_timeout=10)
            self.ssh = ssh
        except Exception as e:  # pragma: no cover
            self.logger.error('failed to connect because: {0}'.format(e))

    def _disconnect(self):
        if self.ssh:
            self.ssh.close()

    def exec_command(self, command):
        pass

    def receive_file(self, f_type):
        # TODO option to receive other files (config can be multiple files)
        if self.host:
            self._connect()
            # TODO better logging
            try:
                scp = SCPClient(self.ssh.get_transport())
                if f_type == 'config':
                    scp.get(self.config_file,
                            local_path=os.path.join(self.config_dir,
                                                    'faucet.yaml'))
                elif f_type == 'log':
                    scp.get(self.log_file,
                            local_path=os.path.join(self.log_dir,
                                                    'faucet.log'))
                else:
                    pass
                scp.close()
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'failed to receive file {0} because: {1}'.format(f_type, e))
            self._disconnect()

    def send_file(self, f_type):
        # TODO option to send other files (config can be multiple files)
        if self.host:
            self._connect()
            # TODO better logging
            try:
                scp = SCPClient(self.ssh.get_transport())
                if f_type == 'config':
                    scp.put(os.path.join(self.config_dir, 'faucet.yaml'),
                            self.config_file)
                elif f_type == 'log':
                    scp.put(os.path.join(self.log_dir, 'faucet.log'),
                            self.log_file)
                else:
                    pass
                scp.close()
            except Exception as e:  # pragma: no cover
                self.logger.error(
                    'failed to send file {0} because: {1}'.format(f_type, e))
            self._disconnect()
