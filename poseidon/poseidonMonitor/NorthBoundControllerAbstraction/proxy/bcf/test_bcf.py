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
Test module for bcf.

@author: kylez
"""
import json
import os

from httmock import HTTMock
from httmock import response
from httmock import urlmatch

from poseidon.baseClasses.Logger_Base import Logger
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.bcf import BcfProxy
from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.bcf.sample_state import span_fabric_state


class MockLogger:
    def __init__(self):
        pass

    def debug(self, msg):
        pass


module_logger = MockLogger()
module_logger.debug('cover this')

cur_dir = os.path.dirname(os.path.realpath(__file__))
username = 'user'
password = 'pass'
cookie = 'cookie'


def mock_factory(regex, filemap):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        if url.path == '/login':
            j = json.loads(request.body)
            assert j['username'] == username
            assert j['password'] == password
            headers = {'set-cookie': 'session_cookie={0}'.format(cookie)}
            r = response(headers=headers, request=request)
        elif url.path in filemap:
            with open(os.path.join(cur_dir, filemap[url.path])) as f:
                data = f.read().replace('\n', '')
            r = response(content=data, request=request)
        else:  # pragma: no cover
            raise Exception('Invalid URL: {0}' .format(url))
        return r
    return mock_fn


def mock_factory2(regex):
    @urlmatch(netloc=regex)
    def mock_fn(url, request):
        if url.path == "/data/controller/applications/bcf/tenant[name=%22TENANT%22]/segment[name=%22SEGMENT%22]/endpoint":
            with open(os.path.join(cur_dir, "sample_endpoints2.json")) as f:
                data = f.read().replace('\n', '')
                data = json.loads(data)
            request_body = json.loads(request.body)
            if request_body["shutdown"]:
                data[0]["state"] = "Shut Down"
            else:
                data[0]["state"] = "Active"
            data = json.dumps(data)
            r = response(content=data, request=request)
        elif url.path == "/data/controller/applications/bcf/span-fabric[name=%22vent%22]" and request.method == "GET":
            data = json.dumps(span_fabric_state)
            r = response(content=data, request=request)
        elif url.path == "/data/controller/applications/bcf/span-fabric[name=%22vent%22]" and request.method == "PUT":
            request_body = json.loads(request.body)
            span_fabric_state[0]["filter"] = request_body["filter"]
            data = json.dumps(span_fabric_state)
            r = response(content=data, request=request)
        else:  # pragma: no cover
            raise Exception('Invalid URL: {0}'.format(url))
        return r
    return mock_fn


def test_BcfProxy():
    """
    Tests bcf
    """
    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
        assert endpoints
        switches = proxy.get_switches()
        assert switches
        tenants = proxy.get_tenants()
        assert tenants
        segments = proxy.get_segments()
        assert segments
        span_fabric = proxy.get_span_fabric()
        assert span_fabric
        span_fabric = proxy.get_span_fabric(span_name="vent")
        assert span_fabric

    with HTTMock(mock_factory2(r'.*')):
        # Normally shutdown_endpoint does not return a value.
        # You should call get_endpoint() afterwards to verify that a shutdown request went through.
        # In addition, the mock endpoint generated does not check for duplicates.
        # TODO: ***This code below is temporary.***
        r = proxy.shutdown_endpoint(
            tenant="TENANT",
            segment="SEGMENT",
            endpoint_name="test",
            mac="00:00:00:00:00:00",
            shutdown=True)
        assert r
        r = proxy.shutdown_endpoint(
            tenant="TENANT",
            segment="SEGMENT",
            endpoint_name="test",
            mac="00:00:00:00:00:00",
            shutdown=False)
        assert r

        r = proxy.mirror_traffic(
            seq=2,
            mirror=True,
            tenant="TENANT",
            segment="SEGMENT")
        assert r
        r = proxy.mirror_traffic(seq=2, mirror=False)
        assert r

    def r(): return True
    r.text = ""

    # cover object
    assert r()

    BcfProxy.parse_json(r)

    proxy.session.cookies.clear_session_cookies()

    proxy.base_uri = "http://jsonplaceholder.typicode.com"
    r = proxy.post_resource('posts')
    r.raise_for_status()
    r = proxy.request_resource(
        method="PUT",
        url="http://jsonplaceholder.typicode.com/posts/1")
    r.raise_for_status()


def test_format_endpoints():
    input_data = list([{'attachment-point': {'switch-interface': {'interface': 'ethernet16',
                                                                  'switch': 'leaf02'},
                                             'type': 'switch-interface'},
                        'attachment-point-state': 'learned',
                        'created-since': '2017-09-18T16:28:34.694Z',
                        'detail': 'true',
                        'interface': 'ethernet16',
                        'ip-address': [{'ip-address': '10.0.0.101',
                                        'ip-state': 'learned',
                                        'mac': 'f8:b1:56:fe:f2:de',
                                        'segment': 'prod',
                                        'tenant': 'FLOORPLATE'}],
                        'leaf-group': '00:00:f4:8e:38:16:a3:73',
                        'mac': 'f8:b1:56:fe:f2:de',
                        'nat-endpoint': False,
                        'remote': False,
                        'segment': 'prod',
                        'state': 'Active',
                        'switch': 'leaf02',
                        'tenant': 'FLOORPLATE',
                        'vlan': -1},
                       {'attachment-point': {'switch-interface': {'interface': 'ethernet42',
                                                                  'switch': 'leaf01'},
                                             'type': 'switch-interface'},
                        'attachment-point-state': 'learned',
                        'created-since': '2017-07-11T23:56:23.888Z',
                        'detail': 'true',
                        'interface': 'ethernet42',
                        'leaf-group': '00:00:f4:8e:38:16:b3:73',
                        'mac': '20:4c:9e:5f:e3:a3',
                        'nat-endpoint': False,
                        'remote': False,
                        'segment': 'to-core-router',
                        'state': 'Active',
                        'switch': 'leaf01',
                        'tenant': 'EXTERNAL',
                        'vlan': -1}])

    output = BcfProxy.format_endpoints(input_data)
    answer = list([{'ip-address': '10.0.0.101', 'mac': 'f8:b1:56:fe:f2:de',
                    'segment': 'prod', 'tenant': 'FLOORPLATE', 'name': None}])
    assert str(answer) == str(output)


def test_get_byip():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None

        def get_endpoints(self):
            return self.endpoints

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
    bcf.endpoints = endpoints
    ret_val = bcf.get_byip('10.0.0.1')
    answer = list([{'ip-address': '10.0.0.1',
                    'ip-state': 'learned',
                    'mac': '00:00:00:00:00:01',
                    'segment': 'poseidon',
                    'tenant': 'poseidon',
                    'name': None}])
    assert str(answer) == str(ret_val)


def test_get_bymac():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None

        def get_endpoints(self):
            return self.endpoints

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
    bcf.endpoints = endpoints
    ret_val = bcf.get_bymac('00:00:00:00:00:01')
    answer = list([{'mac': '00:00:00:00:00:01', 'name': None,
                    'tenant': 'poseidon', 'segment': 'poseidon'}])
    assert str(answer) == str(ret_val)


def test_shutdown_ip():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None

        def get_endpoints(self):
            return self.endpoints

        def shutdown_endpoint(self, tenant, segment, name, mac, shutdown):
            pass

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()

    bcf.endpoints = endpoints
    ret_val = bcf.shutdown_ip('10.0.0.1')
    answer = list([{'ip-address': '10.0.0.1',
                    'ip-state': 'learned',
                    'mac': '00:00:00:00:00:01',
                    'segment': 'poseidon',
                    'tenant': 'poseidon',
                    'name': None}])

    assert str(answer) == str(ret_val)

    ret_val = bcf.shutdown_ip('10.0.0.1', mac_addr='00:00:00:00:00:01')
    answer = list([{'mac': '00:00:00:00:00:01',
                    'name': None,
                    'tenant': 'poseidon',
                    'segment': 'poseidon'}])

    assert str(answer) == str(ret_val)


def test_get_highest():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None
            self.span_fabric = None

       # def get_endpoints(self):
       #     return self.endpoints

       # def get_span_fabric(self):
       #     return self.span_fabric

       # def shutdown_endpoint(self, tenant, segment, name, mac, shutdown):
       #     pass

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    span_fabric = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
        span_fabric = proxy.get_span_fabric()

    bcf.endpoints = endpoints
    bcf.span_fabric = span_fabric
    ret_val = bcf.get_highest(span_fabric)
    answer = 3

    assert answer == ret_val


def test_get_seq_by_ip():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None
            self.span_fabric = None

        # def get_endpoints(self):
        #    return self.endpoints

        def get_span_fabric(self):
            return self.span_fabric

        # def shutdown_endpoint(self, tenant, segment, name, mac, shutdown):
        #    pass

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    span_fabric = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
        span_fabric = proxy.get_span_fabric()

    bcf.endpoints = endpoints
    bcf.span_fabric = span_fabric
    ret_val = bcf.get_seq_by_ip('10.0.0.2')
    answer = list()
    assert answer == ret_val


def test_mirror_ip():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None
            self.span_fabric = None

        # def get_endpoints(self):
        #    return self.endpoints

        def mirror_traffic(
                self,
                seq,
                mirror=True,
                span_name='vent',
                s_dict=None,
                fabric_span_endpoint='',
                **target_kwargs):
            pass

        def get_span_fabric(self):
            return self.span_fabric

        def bad_get_highest(self, spanFabric):
            return None

        # def shutdown_endpoint(self, tenant, segment, name, mac, shutdown):
        #    pass

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }

    proxy = None
    endpoints = None
    span_fabric = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
        span_fabric = proxy.get_span_fabric()

    bcf.endpoints = endpoints
    bcf.span_fabric = span_fabric
    ret_val = bcf.mirror_ip('10.0.0.2')

    bcf.get_highest = bcf.bad_get_highest
    ret_val = bcf.mirror_ip('10.0.0.2')


def test_unmirror_ip():

    class MockBcfProxy(BcfProxy):

        def __init__(self):
            self.endpoints = None
            self.span_fabric = None

        # def get_endpoints(self):
        #    return self.endpoints

        # def mirror_traffic(self, seq, mirror=True, span_name='vent', s_dict=None, fabric_span_endpoint='', **target_kwargs):
        #    pass

        def get_span_fabric(self):
            return self.span_fabric

        # def shutdown_endpoint(self, tenant, segment, name, mac, shutdown):
        #    pass

    bcf = MockBcfProxy()

    filemap = {
        '/data/controller/applications/bcf/info/fabric/switch': 'sample_switches.json',
        '/data/controller/applications/bcf/info/endpoint-manager/tenant': 'sample_tenants.json',
        '/data/controller/applications/bcf/info/endpoint-manager/segment': 'sample_segments.json',
        '/data/controller/applications/bcf/info/endpoint-manager/endpoint': 'sample_endpoints.json',
        '/data/controller/applications/bcf/span-fabric': 'sample_span_fabric.json',
        # %22 = url-encoded double quotes
        '/data/controller/applications/bcf/span-fabric[name=%22vent%22]': 'sample_span_fabric.json',
    }
    proxy = None
    endpoints = None
    span_fabric = None
    with HTTMock(mock_factory(r'.*', filemap)):
        proxy = BcfProxy('http://localhost', 'login',
                         {'username': username, 'password': password})

        endpoints = proxy.get_endpoints()
        span_fabric = proxy.get_span_fabric()

    bcf.endpoints = endpoints
    bcf.span_fabric = span_fabric
    ret_val = bcf.unmirror_ip('10.0.0.2')
