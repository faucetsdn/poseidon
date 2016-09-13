import ast
import json
import uuid

import redis
import web
from docker import Client


class CreateR:
    """
    This endpoint is for creating a new filter
    """

    @staticmethod
    def POST():
        web.header('Content-Type', 'application/json')

        # verify payload is in the correct format
        data = web.data()
        payload = {}
        try:
            payload = ast.literal_eval(data)
            if type(payload) != dict:
                payload = ast.literal_eval(json.loads(data))
        except:
            # !! TODO parse out url parms...
            return 'malformed json body'

        # payload should have the following fields:
        # - id
        # - nic
        # - interval
        # - filter
        # - iters
        # should spin up a tcpdump container that writes out pcap files based on the filter
        # needs to be attached to the nic specified, if iters is -1 then loops until killed,
        # otherwise completes iters number of captures (and creates that many pcap files)
        # should keep track of container id, container name, and id of filter
        # and filter + whatever else is in payload in redis

        # verify payload has necessary information
        if 'nic' not in payload:
            return 'payload missing nic'
        if 'id' not in payload:
            return 'payload missing id'
        if 'interval' not in payload:
            return 'payload missing interval'
        if 'filter' not in payload:
            return 'payload missing filter'
        if 'iters' not in payload:
            return 'payload missing iters'

        # connect to redis
        r = None
        try:
            r = redis.StrictRedis(host='redis', port=6379, db=0)
        except:
            return 'unable to connect to redis'

        # connect to docker
        c = None
        try:
            c = Client(base_url='unix://var/run/docker.sock')
        except:
            return 'unable to connect to docker'

        # store payload in redis
        if r:
            uid = str(uuid.uuid4())
            # !! TODO

        # spin up container with payload specifications
        if c:
            network_config = c.create_host_config(
                network_mode='host', binds=['/files:/files:rw'])
            container = c.create_container(image='collectors/passive-nfilter/nprocessor',
                                           command='/tmp/run.sh ' + payload['nic'] + ' ' + payload[
                                               'interval'] + ' ' + payload['id'] + ' ' + payload[
                                               'filter'] + ' ' + payload['iters'],
                                           host_config=network_config)
            response = c.start(container=container.get('Id'))

        return 'successfully created and started filter ' + str(payload['id'])
