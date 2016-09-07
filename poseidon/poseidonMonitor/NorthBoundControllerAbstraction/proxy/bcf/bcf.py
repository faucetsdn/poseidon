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

    def get_endpoints(self, endpoints_resource='data/controller/applications/bcf/info/endpoint-manager/endpoint'):
        """
        GET list of endpoints from the controller.
        """
        r = self.get_resource(endpoints_resource)
        retval = JsonMixin.parse_json(r)
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

    """ NOTES: big chunk of commented out code of other attempts to try to control
    switch

    def restrict_endpoint(self, tenant, policy_list, action, seqs, endpoint_cidr):
        # seq is a list of 4 seqs
        response = []

        # 1 permit endpoint to EXTERNAL
        r = self.add_policy(tenant=tenant, policy_list=policy_list, action="deny", seq=seq[0],
                            src_tenant=tenant, src_cidr=endpoint_cidr, dst_tenant="EXTERNAL", dst_cidr=None)
        response.append(r)

        # 2 permit EXTERNAL to endpoint
        r = self.add_policy(tenant=tenant, policy_list=policy_list, action="deny", seq=seq[1],
                            src_tenant="EXTERNAL", src_cidr=None, dst_tenant=tenant, dst_cidr=endpoint_cidr)
        response.append(r)

        # 3 deny endpoint to any
        r = self.add_policy(tenant=tenant, policy_list=policy_list, action="deny", seq=seq[2],
                            src_tenant=tenant, src_cidr=endpoint_cidr, dst_tenant=None, dst_cidr=None)
        response.append(r)

        # 4 deny any to endpoint
        r = self.add_policy(tenant=tenant, policy_list=policy_list, action="deny", seq=seq[3],
                            src_tenant=None, src_cidr=None, dst_tenant=tenant, dst_cidr=endpoint_cidr)
        response.append(r)

        return response

    def unrestrict_endpoint(self, tenant, policy_list, policy_list_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]"):
        subs = (tenant, policy_list)
        resource = del_policy_endpoint
        r = self.request_resource(method="DELETE", url=resource)


    def add_policy(self, tenant, policy_list, action, seq, src_tenant, src_cidr, dst_tenant, dst_cidr,
                   add_policy_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]/rule"):

        # TODO ensure default route is set.
        l = [add_policy_endpoint, ]
        l.append("[action=\"%s\"]")
        l.append("[seq=%s]")
        data = {"seq": seq, "action": action}
        src = {}
        dst = {}
        if src_tenant:
            l.append("[src/tenant=\"%s\"]" % src_tenant)
            src["tenant"] = src_tenant
        if src_cidr:
            l.append("[src/cidr=\"%s\"]" % src_cidr)
            src["cidr"] = src_cidr
        if dst_tenant:
            l.append("[dst/tenant=\"%s\"]" % dst_tenant)
            dst["tenant"] = dst_tenant
        if dst_cidr:
            l.append("[dst/cidr=\"%s\"]" % dst_cidr)
            dst["cidr"] = dst_cidr
        if src:
            data["src"] = src
        if dst:
            data["dst"] = dst

        resource = "".join(l)
        subs = (tenant, policy_list, action, seq)
        resource = resource % subs
        r = self.request_resource(method="PUT", url=resource, data=data)
        return self.parse_json(r)

    def del_policy(self, tenant, policy_list, seq, del_policy_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]/rule[seq=%s]"):
        subs = (tenant, policy_list, seq)
        resource = del_policy_endpoint % subs
        r = self.request_resource(method="DELETE", url=resource)
        return self.parse_json(r)

    def restrict_endpoint(self, tenant, policy_list, seq, endpoint_cidr, restrict=True):
        if restrict:
            r = self.add_policy(tenant=tenant,
                           policy_list=policy_list,
                           action="deny",
                           seq=seq,
                           src_tenant=None,
                           src_cidr=None,
                           dst_tenant=tenant
                           dstsrc_cidr)
            r = self.add_policy(tenant,
                           policy_list,
                           "deny",
                           None,)
            r = self.add_policy(tenant, policy_list, )
        else: # restrict is False
            response = []
            for s in self.record[endpoint_cidr]:
                j = self.del_policy(tenant, policy_list, s)
                response.append(j)
            return response




    def add_policy_list(self, tenant, policy_name, policy_list_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]"):
        subs = (tenant, policy_name)
        resource = policy_list_endpoint % subs
        data = {"name": policy_name}
        r = self.request_resource(method="PUT", url=resource, data=data)
        return self.parse_json(r)

    def delete_policy_list(self, tenant, policy_list, policy_list_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]"):
        subs = (tenant, policy_list)
        resource = policy_list_endpoint % subs
        r = self.request_resource(method="DELETE", url=resource)
        return self.parse_json(r)

    def add_policy(self, tenant, policy_list, action, seq, src_tenant, src_cidr, dst_tenant, dst_cidr,
                   add_policy_endpoint="data/controller/applications/bcf/tenant[name=\"%s\"]/logical-router/policy-list[name=\"%s\"]/rule"):
        # TODO ensure default route is set.
        l = [add_policy_endpoint, ]
        l.append("[action=\"%s\"]")
        l.append("[seq=%s]")
        data = {"seq": seq, "action": action}
        src = {}
        dst = {}
        if src_tenant:
            l.append("[src/tenant=\"%s\"]" % src_tenant)
            src["tenant"] = src_tenant
        if src_cidr:
            l.append("[src/cidr=\"%s\"]" % src_cidr)
            src["cidr"] = src_cidr
        if dst_tenant:
            l.append("[dst/tenant=\"%s\"]" % dst_tenant)
            dst["tenant"] = dst_tenant
        if dst_cidr:
            l.append("[dst/cidr=\"%s\"]" % dst_cidr)
            dst["cidr"] = dst_cidr
        if src:
            data["src"] = src
        if dst:
            data["dst"] = dst
        resource = "".join(l)
        subs = (tenant, policy_list, action, seq)
        resource = resource % subs
        r = self.request_resource(method="PUT", url=resource, data=data)
        return self.parse_json(r)

    def restrict_endpoint(self, tenant, endpoint_cidr):
        ip, mask = endpoint_cidr.split("/")
        policy_name = "restrict_%s_%s" % (ip, mask)
        j = self.add_policy_list(tenant, policy_name)

        j = self.add_policy()


    def unrestrict_endpoint(self, tenant, endpoint_cidr):
        if not (tenant in self.record and endpoint_cidr in self.record[tenant]):
            raise Exception()
        policy_list = self.restrictions[tenant][endpoint_cidr]
        j = self.delete_policy_list(tenant, policy_list)
        return j

    """
