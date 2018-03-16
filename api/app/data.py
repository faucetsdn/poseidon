import falcon
import ast
import io
import json
import mimetypes
import os
import redis
import uuid

from datetime import datetime
from .routes import paths, version


class Endpoints(object):

    def on_get(self, req, resp):
        endpoints = []
        for path in paths():
            endpoints.append(version()+path)

        resp.body = json.dumps(endpoints)
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Info(object):

    def on_get(self, req, resp):
        resp.body = json.dumps({'version': 'v0.1.0'})
        resp.content_type = falcon.MEDIA_TEXT
        resp.status = falcon.HTTP_200


class Network(object):

    def connect_redis(self):
        self.r = None
        try:
            self.r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
        except Exception as e:  # pragma: no cover
            try:
                self.r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
            except Exception as e:  # pragma: no cover
                return (False, 'unable to connect to redis because: ' + str(e))
        return

    def get_dataset(self):
        dataset = []
        self.connect_redis()
        if self.r:
            try:
                ip_addresses = self.r.smembers('ip_addresses')
                for ip_address in ip_addresses:
                    node = {}
                    node['uid'] = str(uuid.uuid4())
                    node['IP'] = ip_address
                    # cheating for now
                    node['subnet'] = '.'.join(ip_address.split('.')[:-1])+".0/24"
                    # setting to unknown for now
                    node['rDNS_host'] = 'Unknown'
                    # set as unknown until it's set below
                    node['mac'] = 'Unknown'
                    node['record'] = {}
                    node['role'] = {}
                    node['os'] = {}
                    try:
                        short_os = None
                        full_os = None
                        endpoint_data = {}
                        labels = []
                        confidences = []
                        ip_info = self.r.hgetall(ip_address)

                        if 'poseidon_hash' in ip_info:
                            try:
                                poseidon_info = self.r.hgetall(ip_info['poseidon_hash'])
                                if 'endpoint_data' in poseidon_info:
                                    endpoint_data = ast.literal_eval(poseidon_info['endpoint_data'])
                                    node['mac'] = endpoint_data['mac']
                            except:
                                pass
                        if 'timestamps' in ip_info:
                            try:
                                timestamps = ast.literal_eval(ip_info['timestamps'])
                                node['record']['source'] = 'poseidon'
                                node['record']['timestamp'] = str(datetime.fromtimestamp(float(timestamps[-1])))
                                ml_info = self.r.hgetall(ip_address+'_'+str(timestamps[-1]))
                                if 'labels' in ml_info:
                                    labels = ast.literal_eval(ml_info['labels'])
                                    node['role']['role'] = labels[0]
                                if 'confidences' in ml_info:
                                    confidences = ast.literal_eval(ml_info['confidences'])
                                    node['role']['confidence'] = int(confidences[0]*100)
                            except:
                                pass
                        if 'short_os' in ip_info:
                            short_os = ip_info['short_os']
                            node['os']['os'] = short_os
                        else:
                            node['os']['os'] = 'Unknown'
                    except:
                        pass
                    dataset.append(node)
            except:
                pass

        return dataset

    def get_configuration(self):
        configuration = {}
        return configuration

    def on_get(self, req, resp):
        network = {}
        dataset = self.get_dataset()
        configuration = self.get_configuration()

        network["dataset"] = dataset
        network["configuration"] = configuration
        resp.body = json.dumps(network, indent=2)
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
