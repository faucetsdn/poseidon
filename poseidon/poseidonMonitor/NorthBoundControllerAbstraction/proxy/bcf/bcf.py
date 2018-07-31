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
'''
Created on 25 July 2016
@author: kylez,dgrossman
'''
import json
from urllib.parse import urljoin

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.cookie.cookieauth import CookieAuthControllerProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.mixins.jsonmixin import JsonMixin
#from poseidon.poseidonMonitor.endPoint import EndPoint

module_logger = Logger
module_logger = module_logger.logger


class BcfProxy(JsonMixin, CookieAuthControllerProxy):

    def __init__(
            self,
            base_uri,
            login_resource='auth/login',
            auth=None,
            span_fabric_name = 'vent',
            interface_group = 'ig1',
            *args,
            **kwargs):
        '''
        Initializes BcfProxy object.

        Example usage:
        bcf = BcfProxy("https://127.0.0.1:8443/api/v1/", auth={"user": "USER", "password": "PASSWORD"})
        '''
        default_auth = {'user': None, 'password': None},
        auth = auth or default_auth

        super(BcfProxy, self).__init__(
            base_uri, login_resource, auth, *args, **kwargs)

        self.span_fabric_name = span_fabric_name
        self.interface_group = interface_group
        self.get_span_fabric()

    @staticmethod
    def format_endpoints(data):
        '''
        return only the information needed for the application
        '''
        ret_list = list()
        for d in data:
            ipa = d.get('ip-address')
            if ipa is not None and ipa[0] is not None:
                ipa[0]['name'] = d.get('name')
                # TODO this should grab 'state': 'Active'
                ipa[0]['active'] = 1
                # TODO this should grab interface
                ipa[0]['port'] = None
                ipa[0].pop('ip-state', None)
                ret_list.append(ipa[0])
        return ret_list

    def get_endpoints(
            self,
            messages=None,
            endpoints_resource='data/controller/applications/bcf/info/endpoint-manager/endpoint'):
        '''
        GET list of endpoints from the controller.
        '''
        r = self.get_resource(endpoints_resource)
        retval = JsonMixin.parse_json(r)
        module_logger.debug('get_endpoints found:')
        items = retval
        for item in items:
            module_logger.debug('{0}:{1}'.format(
                dict(item).get('mac'), dict(item).get('ip-address')))
        return retval

    def get_switches(
            self,
            switches_resource='data/controller/applications/bcf/info/fabric/switch'):
        '''
        GET list of switches from the controller.
        '''
        r = self.get_resource(switches_resource)
        retval = BcfProxy.parse_json(r)
        module_logger.debug('get_switches return:{0}'.format(retval))
        return retval

    def get_tenants(
            self,
            tenant_resource='data/controller/applications/bcf/info/endpoint-manager/tenant'):
        '''
        GET list of tenants from the controller.
        '''
        r = self.get_resource(tenant_resource)
        retval = BcfProxy.parse_json(r)
        sout = 'get_tenants return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_segments(
            self,
            segment_resource='data/controller/applications/bcf/info/endpoint-manager/segment'):
        '''
        GET list of segments from the controller.
        '''
        r = self.get_resource(segment_resource)
        retval = BcfProxy.parse_json(r)
        sout = 'get_segments return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_span_fabric(
            self,
            span_name = '',
            interface_group='',
            span_fabric_resource='data/controller/applications/bcf/span-fabric'):

        if not span_name and self.span_fabric_name:
            span_name = self.span_fabric_name
        if not interface_group and self.interface_group:
            interface_group = self.interface_group

        '''
        GET list of span fabric configuration.

        use this to task mirror_traffic
        '''
        if span_name:
            span_fabric_resource = ''.join(
                [span_fabric_resource, '[name="%s"]' % span_name])
        if interface_group:
            span_fabric_resource = ''.join(
                [span_fabric_resource, '[dest-interface-group="%s"]' % interface_group])
        r = self.get_resource(span_fabric_resource)
        spanArray = BcfProxy.parse_json(r)
        if len(spanArray) == 0:
            module_logger.error("A span fabric with the configured combination of name: {0} and interface group: {1} could not be"
            " found on the designated controller".format(span_name, interface_group))
            retval = {}
        else :
            retval = spanArray[0]
        sout = 'get_span_fabric return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_byip(self, ip_addr):
        '''
        return records about ip addresses from get_endpoints
        to be used by shutdown_ip
        '''
        endpoints = self.get_endpoints()
        match_list = []
        for endpoint in endpoints:
            record = None
            name = endpoint.get('name')
            if 'ip-address' in endpoint:
                record = endpoint['ip-address']
                for rec in record:
                    if rec.get('ip-address') == ip_addr:
                        rec['name'] = name
                        match_list.append(rec)
        return match_list

    def get_bymac(self, mac_addr):
        '''
        return records about mac address from get_endpoints
        '''
        endpoints = self.get_endpoints()
        match_list = []
        for endpoint in endpoints:
            if mac_addr == endpoint.get('mac'):
                record = {}
                for value in ['mac', 'name', 'tenant', 'segment']:
                    record[value] = endpoint.get(value)
                match_list.append(record)
        return match_list

    def shutdown_ip(self, ip_addr, shutdown=True, mac_addr=None):
        if mac_addr is None:
            records = self.get_byip(ip_addr)
        else:
            records = self.get_bymac(mac_addr)
        shutdowns = []
        for record in records:
            tenant = record.get('tenant')
            segment = record.get('segment')
            mac = record.get('mac')
            name = '{0}{1}{2}'.format(tenant, segment, mac).replace(':', '')
            if record.get('name') is not None:
                name = record['name']
            module_logger.debug('bcf shutting down: {0}'.format(record))
            module_logger.debug('t:{0} s:{1} n:{2} m{3} shut:{4}'.format(
                tenant, segment, name, mac, shutdown))
            self.shutdown_endpoint(tenant, segment, name, mac, shutdown)
            shutdowns.append(record)
        return shutdowns

    def shutdown_endpoint(
            self,
            tenant,
            segment,
            endpoint_name,
            mac=None,
            shutdown=True,
            shutdown_resource="data/controller/applications/bcf/tenant[name=\"%s\"]/segment[name=\"%s\"]/endpoint"):
        '''
        PUT to jail (i.e. isolate) an endpoint from the network.

        Jail with shutdown=True, unjail by shutdown=False.

        if the endpoint_name is not currently named, you must supply the mac addr
        and make up an endpoint name

        if there is an endpoint name, only need endpoint_name

        '''
        subs = (tenant, segment)
        resource = shutdown_resource % subs
        uri = urljoin(self.base_uri, resource)
        data = {'shutdown': shutdown, 'name': endpoint_name}
        if mac:
            data['mac'] = mac
        r = self.request_resource(method='PUT', url=uri, data=json.dumps(data))
        retval = BcfProxy.parse_json(r)
        sout = 'shutdown_endpoint return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    @staticmethod
    def get_highest(span_fabric):
        '''
        get the max number, should be all clear after it
        '''
        my_filter = span_fabric.get('filter')
        if my_filter is not None:
            my_max = -1
            for f in my_filter:
                seq = int(f.get('seq', -2))
                if int(seq) > my_max:
                    my_max = seq
            return (my_max + 1)
        else:
            module_logger.debug('noFilters online')
            return 1

    def get_seq_by_ip(self, ip):
        my_filter = self.get_span_fabric().get('filter')
        retval = []
        if my_filter is not None:
            for f in my_filter:
                if 'match-specification' in f:
                    dst = f[
                        'match-specification'].get('dst-ip-cidr', 'broke')[:-3]
                    src = f[
                        'match-specification'].get('src-ip-cidr', 'broke')[:-3]
                    if src == ip or dst == ip:
                        retval.append(f.get('seq'))
        return retval

    def mirror_ip(self, ip, messages=None):
        my_start = self.get_highest(self.get_span_fabric())
        if my_start is not None:
            module_logger.debug('mirroring {0}'.format(my_start))
            src = {'match-specification': {'src-ip-cidr': '{0}/32'.format(ip)}}
            dst = {'match-specification': {'dst-ip-cidr': '{0}/32'.format(ip)}}
            self.mirror_traffic(my_start, mirror=True, s_dict=src)
            self.mirror_traffic(my_start + 1, mirror=True, s_dict=dst)
        else:
            module_logger.error('mirror_ip:None')

    def unmirror_ip(self, ip, messages=None):
        kill_list = self.get_seq_by_ip(ip)
        for kill in kill_list:
            module_logger.debug('unmirror:{0}'.format(kill))
            self.mirror_traffic(kill, mirror=False)

    def mirror_traffic(
            self,
            seq,
            mirror=True,
            span_name='vent',
            s_dict=None,
            fabric_span_endpoint="data/controller/applications/bcf/span-fabric[name=\"{0}\"]",
            **target_kwargs):
        '''
        mirror_traffic doc string
        '''

        '''
        mirror_traffic(q,mirror=True,s_dict = {'match-specificaiton' : {'dst-ip-cidr':'10.179.0.33/32'} ...
        NOTE: s_dict or kwargs, not both..


        If mirror=True, PUT to apply the filter rules specified by target_kwargs
        to a specified span fabric (vent by default).  For example,
        bcf.mirror_traffic(seq=1, tenant="TENANT", segment="SEGMENT")
        will apply a rule with seq=1 filtering all traffic matching tenant
        TENANT and segment SEGMENT. If a rule with seq=1 already exists, it will
        be overwritten.

        If mirror=False, PUT to delete the rule with specified seq.
        If no such rule exists, this call does nothing.
        "src-ip-cidr": "X.A.0.33/32:"

        {
            "name": "vent",
            "active": true,
            "priority": 1,
            "dest-interface-group": "ig1",
            "filter": [
                  {#sDict
                            "match-specification": {
                                        "dst-ip-cidr": "X.A.0.33/32"
                                      },
                            "seq": 7
                          },
                  {
                            "match-specification": {
                                        "src-ip-cidr": "X.A.0.33/32"
                                      },
                            "seq": 8
                          },
                  {
                            "match-specification": {
                                        "src-mac": "AA:AA:AA:AA:AA:AA"
                                      },
                            "seq": 9
                          },
                  {#kwargs way
                            "seq": 10,
                            "tenant": "port2",
                            "segment": "prod"
                          }
                ]
          }

        '''
        resource = fabric_span_endpoint.format(self.span_fabric_name)
        uri = urljoin(self.base_uri, resource)
        data = self.get_span_fabric()  # first element is vent span rule
        module_logger.debug('{0}'.format(data))
        if mirror:
            new_filter = {}
            if s_dict is not None:
                new_filter.update(s_dict)
            else:
                new_filter.update(target_kwargs)
            new_filter['seq'] = seq
            # empty capture list
            if 'filter' not in data:
                data['filter'] = []
            data['filter'].append(new_filter)
        else:  # mirror=False
            data['filter'] = [filter for filter in data[
                'filter'] if filter['seq'] != seq]
        r = self.request_resource(method='PUT', url=uri, data=json.dumps(data))
        retval = BcfProxy.parse_json(r)
        sout = 'mirror_traffic return:{0}'.format(retval)
        module_logger.debug(sout)

        return retval
