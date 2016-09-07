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
Created on 25 July 2016
@author: kylez,dgrossman
"""
import json
import logging
from urlparse import urljoin

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.auth.cookie.cookieauth import CookieAuthControllerProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.mixins.jsonmixin import JsonMixin

module_logger = logging.getLogger(__name__)


class BcfProxy(JsonMixin, CookieAuthControllerProxy):

    def __init__(self, base_uri, login_resource='auth/login', auth={'user': None, 'password': None}, *args, **kwargs):
        """
        Initializes BcfProxy object.

        Example usage:
        bcf = BcfProxy("https://127.0.0.1:8443/api/v1/", auth={"user": "USER", "password": "PASSWORD"})
        """
        super(BcfProxy, self).__init__(
            base_uri, login_resource, auth, *args, **kwargs)

    @staticmethod
    def reduce_endpoints(data):
        ret_list = list()
        for d in data:
            ipa = d.get('ip-address')
            if ipa is not None and ipa[0] is not None:
                ipa[0]['name'] = d.get('name')
                ipa[0].pop('ip-state', None)
                ret_list.append(ipa[0])
        return ret_list

    def get_endpoints(self, endpoints_resource='data/controller/applications/bcf/info/endpoint-manager/endpoint'):
        """
        GET list of endpoints from the controller.
        """
        r = self.get_resource(endpoints_resource)
        retval = self.reduce_endpoints(JsonMixin.parse_json(r))
        sout = 'get_endpoints return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_switches(self, switches_resource='data/controller/applications/bcf/info/fabric/switch'):
        """
        GET list of switches from the controller.
        """
        r = self.get_resource(switches_resource)
        retval = BcfProxy.parse_json(r)
        module_logger.debug('get_switches return:{0}'.format(retval))
        return retval

    def get_tenants(self, tenant_resource='data/controller/applications/bcf/info/endpoint-manager/tenant'):
        """
        GET list of tenants from the controller.
        """
        r = self.get_resource(tenant_resource)
        retval = BcfProxy.parse_json(r)
        sout = 'get_tenants return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_segments(self, segment_resource='data/controller/applications/bcf/info/endpoint-manager/segment'):
        """
        GET list of segments from the controller.
        """
        r = self.get_resource(segment_resource)
        retval = BcfProxy.parse_json(r)
        sout = 'get_segments return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def get_span_fabric(self, span_name=None, span_fabric_resource='data/controller/applications/bcf/span-fabric'):
        """
        GET list of span fabric configuration.

        use this to task mirror_traffic
        """
        if span_name:
            span_fabric_resource = ''.join(
                [span_fabric_resource, '[name="%s"]' % span_name])
        r = self.get_resource(span_fabric_resource)
        retval = BcfProxy.parse_json(r)
        sout = 'get_span_fabric return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval

    def shutdown_endpoint(self, tenant, segment, endpoint_name, mac=None, shutdown=True, shutdown_resource="data/controller/applications/bcf/tenant[name=\"%s\"]/segment[name=\"%s\"]/endpoint"):
        """
        PUT to jail (i.e. isolate) an endpoint from the network.

        Jail with shutdown=True, unjail by shutdown=False.

        if the endpoint_name is not currently named, you must supply the mac addr
        and make up an endpoint name

        if there is an endpoint name, only need endpoint_name

        """
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

    def mirror_traffic(self, seq, mirror=True, span_name='vent', fabric_span_endpoint="data/controller/applications/bcf/span-fabric[name=\"%s\"]", **target_kwargs):
        """

        If mirror=True, PUT to apply the filter rules specified by target_kwargs to a specified span fabric (vent by default). For example, bcf.mirror_traffic(seq=1, tenant="TENANT", segment="SEGMENT") will apply a rule with seq=1 filtering all traffic matching tenant TENANT and segment SEGMENT. If a rule with seq=1 already exists, it will be overwritten.

        If mirror=False, PUT to delete the rule with specified seq. If no such rule exists, this call does nothing.
        """
        resource = fabric_span_endpoint % span_name
        uri = urljoin(self.base_uri, resource)
        data = self.get_span_fabric()[0]  # first element is vent span rule
        if mirror:
            new_filter = target_kwargs
            new_filter['seq'] = seq
            data['filter'].append(target_kwargs)
        else:  # mirror=False
            data['filter'] = [filter for filter in data[
                'filter'] if filter['seq'] != seq]
        r = self.request_resource(method='PUT', url=uri, data=json.dumps(data))
        retval = BcfProxy.parse_json(r)
        sout = 'mirror_traffic return:{0}'.format(retval)
        module_logger.debug(sout)
        return retval
