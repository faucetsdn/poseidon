#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The commands that can be executed in the Poseidon shell.

Created on 18 January 2019
@author: Charlie Lewis
"""
from poseidon.main import SDNConnect


class Commands:

    def __init__(self):
        self.states = ['active', 'inactive', 'known', 'unknown',
                       'mirroring', 'abnormal', 'shutdown', 'reinvestigating', 'queued']
        self.sdnc = SDNConnect()

    def what_is(self, args):
        ''' what is a specific thing '''
        eps = []
        device = args.rsplit(' ', 1)[-1]
        eps.append(self.sdnc.endpoint_by_name(device))
        eps.append(self.sdnc.endpoint_by_hash(device))
        eps += self.sdnc.endpoints_by_ip(device)
        eps += self.sdnc.endpoints_by_mac(device)
        endpoints = []
        for endpoint in eps:
            if endpoint:
                info = self.sdnc.what_is(endpoint)
                endpoints.append((endpoint, info))
        return endpoints

    def where_is(self, args):
        ''' where topologically is a specific thing '''
        eps = []
        device = args.rsplit(' ', 1)[-1]
        eps.append(self.sdnc.endpoint_by_name(device))
        eps.append(self.sdnc.endpoint_by_hash(device))
        eps += self.sdnc.endpoints_by_ip(device)
        eps += self.sdnc.endpoints_by_mac(device)
        endpoints = []
        for endpoint in eps:
            if endpoint:
                info = self.sdnc.where_is(endpoint)
                endpoints.append((endpoint, info))
        return endpoints

    def collect_on(self, args):
        ''' collect on a specific thing '''
        eps = []
        device = args.rsplit(' ', 1)[-1]
        eps.append(self.sdnc.endpoint_by_name(device))
        eps.append(self.sdnc.endpoint_by_hash(device))
        eps += self.sdnc.endpoints_by_ip(device)
        eps += self.sdnc.endpoints_by_mac(device)
        endpoints = []
        for endpoint in eps:
            if endpoint:
                self.sdnc.collect_on(endpoint)
                endpoints.append(endpoint)
        return endpoints

    def remove_inactives(self, args):
        ''' remove all inactive devices '''
        return self.sdnc.remove_inactive_endpoints()

    def remove_ignored(self, args):
        ''' remove all ignored devices '''
        return self.sdnc.remove_ignored_endpoints()

    def ignore(self, args):
        ''' ignore a specific thing '''
        eps = []
        device = args.rsplit(' ', 1)[0]
        if device == 'inactive':
            for endpoint in self.sdnc.endpoints:
                if endpoint.state == 'inactive':
                    eps.append(endpoint)
        else:
            eps.append(self.sdnc.endpoint_by_name(device))
            eps.append(self.sdnc.endpoint_by_hash(device))
            eps += self.sdnc.endpoints_by_ip(device)
            eps += self.sdnc.endpoints_by_mac(device)

        endpoints = []
        for endpoint in eps:
            if endpoint:
                self.sdnc.ignore_endpoint(endpoint)
                endpoints.append(endpoint)
        return endpoints

    def clear_ignored(self, args):
        ''' stop ignoring a specific thing '''
        eps = []
        device = args.rsplit(' ', 1)[0]
        if device == 'ignored':
            for endpoint in self.sdnc.endpoints:
                if endpoint.ignore:
                    eps.append(endpoint)
        else:
            eps.append(self.sdnc.endpoint_by_name(device))
            eps.append(self.sdnc.endpoint_by_hash(device))
            eps += self.sdnc.endpoints_by_ip(device)
            eps += self.sdnc.endpoints_by_mac(device)

        endpoints = []
        for endpoint in eps:
            if endpoint:
                self.sdnc.clear_ignored_endpoint(endpoint)
                endpoints.append(endpoint)
        return endpoints

    def remove(self, args):
        ''' remove and forget about a specific thing until it's seen again '''
        eps = []
        device = args.rsplit(' ', 1)[0]
        eps.append(self.sdnc.endpoint_by_name(device))
        eps.append(self.sdnc.endpoint_by_hash(device))
        eps += self.sdnc.endpoints_by_ip(device)
        eps += self.sdnc.endpoints_by_mac(device)
        endpoints = []
        for endpoint in eps:
            if endpoint:
                self.sdnc.remove_endpoint(endpoint)
                endpoints.append(endpoint)
        return endpoints

    def show_devices(self, args):
        '''
        show all devices that are of a specific filter. i.e. windows,
        developer workstation, abnormal, mirroring, etc.
        '''
        state = None
        type_filter = None
        all_devices = False
        query = args.rsplit(' ', 1)[0]
        if query in self.states:
            state = query
        elif query == 'all':
            all_devices = True
        else:
            type_filter = query
        return self.sdnc.show_endpoints(state, type_filter, all_devices)
