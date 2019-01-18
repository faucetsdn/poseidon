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

    def what_is(self, args):
        ''' what is a specific thing '''
        return

    def where_is(self, args):
        ''' where topologically is a specific thing '''
        return

    def collect_on(self, args):
        ''' collect on a specific thing '''
        return

    def remove_inactives(self, args):
        ''' remove all inactive devices '''
        return

    def remove_ignored(self, args):
        ''' remove all ignored devices '''
        return

    def ignore(self, args):
        ''' ignore a specific thing '''
        return

    def show_ignored(self, args):
        ''' show all things that are being ignored '''
        endpoints = []
        sdnc = SDNConnect()
        sdnc.get_stored_endpoints()
        for endpoint in sdnc.endpoints:
            if endpoint.ignore:
                endpoints.append(endpoint)
        return endpoints

    def clear_ignored(self, args):
        ''' stop ignoring a specific thing '''
        return

    def remove(self, args):
        ''' remove and forget about a specific thing until it's seen again '''
        return

    def show_devices(self, args):
        '''
        show all devices that are of a specific filter. i.e. windows,
        developer workstation, abnormal, mirroring, etc.
        '''
        state = None
        type_filter = None
        query = args.rsplit(' ', 1)[0]
        if query in self.states:
            state = query
        else:
            type_filter = query
        endpoints = []
        sdnc = SDNConnect()
        sdnc.get_stored_endpoints()
        for endpoint in sdnc.endpoints:
            if state:
                if endpoint.state == state:
                    endpoints.append(endpoint)
            elif type_filter:
                # TODO
                pass
        return endpoints
