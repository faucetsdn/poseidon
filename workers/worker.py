import datetime
import json
import os
import time
import uuid

import docker
import pika
from prometheus_client import Enum
from prometheus_client import start_http_server


def set_status(status):
    for worker in status:
        metrics[worker].state(status[worker]['state'])


def callback(ch, method, properties, body, workers_json='workers.json'):
    """Callback that has the message that was received"""
    vol_prefix = os.getenv('VOL_PREFIX', '')
    workers = load_workers(workers_json)
    d = setup_docker()
    pipeline = json.loads(body.decode('utf-8'))
    worker_found = False
    status = {}
    for worker in workers['workers']:
        file_path = pipeline['file_path']
        if file_path in ['-1', '']:
            print(' [X file empty] %s UTC %r:%r' % (str(datetime.datetime.utcnow()),
                                                    method.routing_key,
                                                    pipeline))
        elif 'id' in pipeline and (('results' in pipeline and pipeline['results']['tool'] in worker['inputs']) or ('file_type' in pipeline and pipeline['file_type'] in worker['inputs'])):
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

            use_swarm = os.getenv('SWARM', '0')
            try:
                if use_swarm == '1':
                    # fix environment
                    env = []
                    for key in environment:
                        if key != 'results':
                            env.append(key+'='+str(environment[key]))
                    restart_policy = docker.types.RestartPolicy()
                    d.services.create(image=image,
                                      name=name,
                                      networks=[worker['stage']],
                                      constraints=['node.role==worker'],
                                      restart_policy=restart_policy,
                                      labels={'project': 'poseidon'},
                                      mounts=[vol_prefix +
                                              '/opt/poseidon_files:/files:rw'],
                                      env=env,
                                      args=command)
                else:
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
                status[worker['name']] = {'state': 'In progress'}
                worker_found = True
            except Exception as e:  # pragma: no cover
                print('failed: {0}'.format(str(e)))
                status[worker['name']] = {'state': 'Error'}
        else:
            if not worker['name'] in status:
                status[worker['name']] = {'state': 'Queued'}
    if 'id' in pipeline and 'results' in pipeline and pipeline['type'] == 'data':
        print(' [Data] %s UTC %r:%r:%r' % (str(datetime.datetime.utcnow()),
                                           method.routing_key,
                                           pipeline['id'],
                                           pipeline['results']))
        status[pipeline['results']['tool']] = {'state': 'In progress'}
    elif 'id' in pipeline and 'results' in pipeline and pipeline['type'] == 'metadata':
        if 'data' in pipeline and pipeline['data'] != '':
            print(' [Metadata] %s UTC %r:%r:%r' % (str(datetime.datetime.utcnow()),
                                                   method.routing_key,
                                                   pipeline['id'],
                                                   pipeline['results']))
            status[pipeline['results']['tool']] = {'state': 'In progress'}
        else:
            print(' [Finished] %s UTC %r:%r' % (str(datetime.datetime.utcnow()),
                                                method.routing_key,
                                                pipeline))
            status[pipeline['results']['tool']] = {'state': 'Complete'}
    elif not worker_found:
        print(' [X no match] %s UTC %r:%r' % (str(datetime.datetime.utcnow()),
                                              method.routing_key,
                                              pipeline))

    ch.basic_ack(delivery_tag=method.delivery_tag)
    set_status(status)


def main(queue_name, host):  # pragma: no cover
    """Creates the connection to RabbitMQ as a consumer and binds to the queue
    waiting for messages
    """
    start_prom()
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


def start_prom(port=9305):
    start_http_server(port)


def init_metrics(workers):
    metrics = {}
    for worker in workers:
        metrics[worker] = Enum(worker.replace('-', '_')+'_state',
                               'State of worker '+worker,
                               states=['In progress',
                                       'Queued',
                                       'Error',
                                       'Complete'])
    return metrics


def load_workers(workers_json='workers.json'):
    with open(workers_json) as json_file:
        workers = json.load(json_file)
    return workers


if __name__ == '__main__':  # pragma: no cover
    global metrics
    queue_name = os.getenv('RABBIT_QUEUE_NAME', 'task_queue')
    host = os.getenv('RABBIT_HOST', 'messenger')
    workers = load_workers()
    metrics = init_metrics(workers)
    main(queue_name, host)
