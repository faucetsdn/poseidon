import datetime
import json
import os
import time
import uuid

import docker
import pika
from redis import StrictRedis


def save(r, tool, results):
    timestamp = str(int(time.time()))
    if tool not in ['p0f']:  # , 'networkml']:
        return
    try:
        if isinstance(results, list):
            for result in results:
                for key in result:
                    redis_k = {}
                    for k in result[key]:
                        redis_k[k] = str(result[key][k])
                    r.hmset(key, redis_k)
                    r.hmset(tool+'_'+timestamp+'_'+key, redis_k)
                    r.sadd('ip_addresses', key)
                    r.sadd(tool+'_timestamps', timestamp)
        elif isinstance(results, dict):
            for key in results:
                redis_k = {}
                for k in results[key]:
                    redis_k[k] = str(results[key][k])
                r.hmset(key, redis_k)
                r.hmset(tool+'_'+timestamp+'_'+key, redis_k)
                r.sadd('ip_addresses', key)
                r.sadd(tool+'_timestamps', timestamp)
    except Exception as e:  # pragma: no cover
        print(
            f'Unable to store contents of {tool}: {results} in redis because: {e}')
    return


def set_status(r, status):
    try:
        r.hmset('status', status)
        statuses = r.hgetall('status')
        for s in statuses:
            statuses[s] = json.loads(statuses[s])
        for worker in extra_workers:
            if worker not in statuses:
                status[worker] = extra_workers[worker]
        r.hmset('status', status)
    except Exception as e:  # pragma: no cover
        print(f'Failed to update Redis because: {e}')
    return


def callback(ch, method, properties, body):
    """Callback that has the message that was received"""
    vol_prefix = os.getenv('VOL_PREFIX', '')
    workers = load_workers()
    d = setup_docker()
    pipeline = json.loads(body.decode('utf-8'))
    worker_found = False
    status = {}
    extra_workers = {}
    r = setup_redis()
    for worker in workers['workers']:
        file_path = pipeline['file_path']
        if 'id' in pipeline and (('results' in pipeline and pipeline['results']['tool'] in worker['inputs']) or ('file_type' in pipeline and pipeline['file_type'] in worker['inputs'])):
            uid = str(uuid.uuid4()).split('-')[-1]
            name = worker['name'] + '_' + uid
            image = worker['image']
            ports = None

            if 'version' in worker:
                image += ':' + worker['version']
            command = []
            if 'command' in worker:
                command = worker['command']

            command.append(file_path)

            environment = pipeline
            if 'environment' in worker:
                environment.update(worker['environment'])
            if 'rabbit' not in pipeline:
                pipeline['rabbit'] = 'true'
            if 'ports' in worker:
                ports = worker['ports']

            keep_images = os.getenv('KEEPIMAGES', '0')
            remove = True
            if keep_images == '1':
                remove = False

            try:
                d.containers.run(image=image,
                                 name=name,
                                 network=worker['stage'],
                                 volumes={
                                     vol_prefix + '/opt/poseidon_files': {'bind': '/files', 'mode': 'rw'}},
                                 environment=environment,
                                 remove=remove,
                                 command=command,
                                 ports=ports,
                                 detach=True)
                print(' [Create container] %s UTC %r:%r:%r:%r' % (str(datetime.datetime.utcnow()),
                                                                  method.routing_key,
                                                                  pipeline['id'],
                                                                  image,
                                                                  pipeline))
                status[worker['name']] = json.dumps(
                    {'state': 'In progress', 'timestamp': str(datetime.datetime.utcnow())})
                worker_found = True
            except Exception as e:  # pragma: no cover
                print('failed: {0}'.format(str(e)))
                status[worker['name']] = json.dumps(
                    {'state': 'Error', 'timestamp': str(datetime.datetime.utcnow())})
        else:
            extra_workers[worker['name']] = json.dumps(
                {'state': 'Queued', 'timestamp': str(datetime.datetime.utcnow())})
    if 'id' in pipeline and 'results' in pipeline and pipeline['type'] == 'data':
        print(' [Data] %s UTC %r:%r:%r' % (str(datetime.datetime.utcnow()),
                                           method.routing_key,
                                           pipeline['id'],
                                           pipeline['results']))
        status[pipeline['results']['tool']] = json.dumps(
            {'state': 'In progress', 'timestamp': str(datetime.datetime.utcnow())})
    elif 'id' in pipeline and 'results' in pipeline and pipeline['type'] == 'metadata':
        if 'data' in pipeline and pipeline['data'] != '':
            print(' [Metadata] %s UTC %r:%r:%r' % (str(datetime.datetime.utcnow()),
                                                   method.routing_key,
                                                   pipeline['id'],
                                                   pipeline['results']))
            save(r, pipeline['results']['tool'], pipeline['data'])
            status[pipeline['results']['tool']] = json.dumps(
                {'state': 'In progress', 'timestamp': str(datetime.datetime.utcnow())})
        else:
            print(' [Finished] %s UTC %r:%r' % (str(datetime.datetime.utcnow()),
                                                method.routing_key,
                                                pipeline))
            status[pipeline['results']['tool']] = json.dumps(
                {'state': 'Complete', 'timestamp': str(datetime.datetime.utcnow())})
    elif not worker_found:
        print(' [X no match] %s UTC %r:%r' % (str(datetime.datetime.utcnow()),
                                              method.routing_key,
                                              pipeline))

    ch.basic_ack(delivery_tag=method.delivery_tag)

    set_status(r, status)
    try:
        r.close()
    except Exception as e:  # pragma: no cover
        print('Failed to close Redis connection because: {0}'.format(str(e)))


def main(queue_name, host):  # pragma: no cover
    """Creates the connection to RabbitMQ as a consumer and binds to the queue
    waiting for messages
    """
    counter = 0
    while True:
        counter += 1
        try:
            params = pika.ConnectionParameters(host=host, port=5672)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            print('Connected to rabbit')
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=queue_name, on_message_callback=callback)
            channel.start_consuming()
        except Exception as e:  # pragma: no cover
            print(str(e))
            print(
                'Waiting for connection to rabbit...attempt: {0}'.format(counter))
        time.sleep(1)

    return


def setup_docker():
    return docker.from_env()


def setup_redis(host='redis', port=6379, db=0):
    r = None
    try:
        r = StrictRedis(host=host, port=port, db=db,
                        socket_connect_timeout=2, decode_responses=True)
    except Exception as e:  # pragma: no cover
        print('Failed connect to Redis because: {0}'.format(str(e)))
    return r


def load_workers():
    with open('workers.json') as json_file:
        workers = json.load(json_file)
    return workers


if __name__ == '__main__':  # pragma: no cover
    queue_name = 'task_queue'
    host = 'messenger'
    main(queue_name, host)
