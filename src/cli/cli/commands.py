#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The commands that can be executed in the Poseidon shell.

Created on 18 January 2019
@author: Charlie Lewis
"""
import json
import logging

from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.controllers.sdnconnect import SDNConnect
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.prometheus import Prometheus

logger = logging.getLogger('commands')


class Commands:

    def __init__(self, config=None, faucetconfgetsetter_cl=FaucetRemoteConfGetSetter):
        self.states = ['known', 'unknown', 'operating', 'queued']
        if config:
            self.config = config
        else:
            self.config = Config().get_config()
        prom = Prometheus()
        self.sdnc = SDNConnect(self.config, logger, prom,
                               faucetconfgetsetter_cl=faucetconfgetsetter_cl)

    def _publish_action(self, address, payload):
        if payload:
            self.sdnc.publish_action(address, json.dumps(payload))

    def _get_endpoints(self, args, idx, match_all=False):
        ''' get endpoints that match '''
        self.sdnc.get_stored_endpoints()
        device = args.rsplit(' ', 1)[idx]
        endpoints = {}
        for match_func in (
                self.sdnc.endpoint_by_name,
                self.sdnc.endpoint_by_hash,
                self.sdnc.endpoints_by_ip,
                self.sdnc.endpoints_by_mac):
            match = match_func(device)
            if match:
                if isinstance(match, list):
                    endpoints.update(
                        {endpoint.name: endpoint for endpoint in match})
                else:
                    endpoints[match.name] = match
                if not match_all:
                    break
        return endpoints.values()

    def _ignored_endpoints(self):
        return [
            endpoint for endpoint in self.sdnc.endpoints.values()
            if endpoint.ignore]

    def what_is(self, args):
        ''' what is a specific thing '''
        return self._get_endpoints(args, -1)

    def history_of(self, args):
        ''' history of a specific thing '''
        return self._get_endpoints(args, -1)

    def acls_of(self, args):
        ''' ACL history of a specific thing '''
        return self._get_endpoints(args, -1)

    def where_is(self, args):
        ''' where topologically is a specific thing '''
        return self._get_endpoints(args, -1)

    def remove_ignored(self, args):
        ''' remove all ignored devices '''
        endpoints = self._ignored_endpoints()
        endpoint_names = [endpoint.name for endpoint in endpoints]
        self._publish_action('poseidon.action.remove.ignored', endpoint_names)
        return endpoints

    def ignore(self, args):
        ''' ignore a specific thing '''
        endpoints = self._get_endpoints(args, 0, match_all=True)
        endpoint_names = [endpoint.name for endpoint in endpoints]
        self._publish_action('poseidon.action.ignore', endpoint_names)
        return endpoints

    def clear_ignored(self, args):
        ''' stop ignoring a specific thing '''
        device = args.rsplit(' ', 1)[0]
        if device == 'ignored':
            endpoints = self._ignored_endpoints()
        else:
            endpoints = self._get_endpoints(args, 0, match_all=True)
        endpoint_names = [endpoint.name for endpoint in endpoints]
        self._publish_action('poseidon.action.clear.ignored', endpoint_names)
        return endpoints

    def remove(self, args):
        ''' remove and forget about a specific thing until it's seen again '''
        endpoints = self._get_endpoints(args, 0)
        endpoint_names = [endpoint.name for endpoint in endpoints]
        self._publish_action('poseidon.action.remove', endpoint_names)
        return endpoints

    def show_devices(self, arg):
        '''
        show all devices that are of a specific filter. i.e. windows,
        developer workstation, mirroring, etc.
        '''
        return self.sdnc.show_endpoints(arg)

    def change_devices(self, args):
        ''' change state of a specific thing '''
        state = args.rsplit(' ', 1)[-1]
        endpoints = self._get_endpoints(args, 0)
        endpoint_names = [(endpoint.name, state) for endpoint in endpoints]
        self._publish_action('poseidon.action.change', endpoint_names)
        return endpoints
