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
Created on 17 May 2016
@author: dgrossman
"""
import functools
import logging

import schedule

from poseidon.baseClasses.enums_tuples import CRONSPEC
from poseidon.baseClasses.enums_tuples import EVERY
from poseidon.baseClasses.Main_Action_Base import Main_Action_Base


module_logger = logging.getLogger(__name__)

'''
def rabbit_init(host, exchange, queue_name):  # pragma: no cover
    """
    Connects to rabbitmq using the given hostname,
    exchange, and queue. Retries on failure until success.
    Binds routing keys appropriate for module, and returns
    the channel and connection.
    """
    wait = True
    while wait:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, type='topic')
            result = channel.queue_declare(queue=queue_name, exclusive=True)
            wait = False
            module_logger.info('connected to rabbitmq...')
            print "connected to rabbitmq..."
        except Exception, e:
            print "waiting for connection to rabbitmq..."
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    binding_keys = sys.argv[1:]
    if not binding_keys:
        ostr = 'Usage: {0} [binding_key]...'.format(sys.argv[0])
        module_logger.error(ostr)
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection

# NOTE: add basic consume to channel
'''


class Scheduler(Main_Action_Base):

    def __init__(self):
        super(Scheduler, self).__init__()
        self.logger = module_logger
        self.mod_name = self.__class__.__name__
        self.schedule = schedule
        self.schedule.clear()
        self.handles = dict()
        self.currentJobs = dict()

    @staticmethod
    def safe(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:  # pragma: no cover
                import traceback
                badness = traceback.format_exc()
                if 'log' in kwargs:
                    kwargs['log'].error(badness)
                else:
                    args[1].error(badness)
        return wrapper

    def do_once(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:  # pragma: no cover
                import traceback
                badness = traceback.format_exc()
                if 'log' in kwargs:
                    kwargs['log'].error(badness)
                else:
                    args[1].error(badness)
            return self.schedule.CancelJob
        return wrapper

    def add_job(self, jobId, cronspec, func, **kwargs):

        occurs = cronspec.occurs
        start = cronspec.starts

        if occurs == EVERY.once:
            if start is not None:
                self.schedule.every().day.at(start).do(self.do_once(func),
                                                       jobId,
                                                       self.logger,
                                                       **kwargs)
            else:
                self.schedule.every().day.do(self.do_once(func),
                                             jobId,
                                             self.logger,
                                             **kwargs)

        if occurs == EVERY.day:
            if start is not None:
                self.schedule.every().day.at(start).do(self.safe(func),
                                                       jobId,
                                                       self.logger,
                                                       **kwargs)
            else:
                self.schedule.every().day.do(self.safe(func),
                                             jobId,
                                             self.actions,
                                             **kwargs)

        if occurs == EVERY.hour:
            if start is not None:
                self.schedule.every().hour.at(start).do(self.safe(func),
                                                        jobId,
                                                        self.logger,
                                                        **kwargs)
            else:
                self.schedule.every().hour.do(self.safe(func),
                                              jobId,
                                              self.logger,
                                              **kwargs)

        if occurs == EVERY.minute:
            if start is not None:
                self.schedule.every(start).minutes.do(self.safe(func),
                                                      jobId,
                                                      self.logger,
                                                      **kwargs)
            else:
                self.schedule.every().minute.do(self.safe(func),
                                                jobId,
                                                self.logger,
                                                **kwargs)

    def del_job(self, jobId):
        for job in self.schedule.jobs:
            for k, v in job.__dict__.iteritems():
                if k == 'job_func':
                    if len(v.args) >= 1:
                        if jobId == v.args[0]:
                            logLine = 'killing: {0}'.format(job)
                            self.logger.debug(logLine)
                            self.schedule.cancel_job(job)
                        else:  # pragma: no cover
                            logLine = '*' * 10
                            self.logger.debug(logLine)
                            jid = v.keywords.get('jobId')
                            if jid == jobId:
                                logLine = 'killing:{0}'.format(job)
                                self.logger.debug(logLine)
                                self.schedule.cancel_job(job)
                                logLine = 'vargs = {0}\nkeyworks = {1}\n{2}\n'.format(
                                    v.args, v.keywords, '-' * 40)
                                self.logger.debug(logLine)

    @staticmethod
    def get_jobId(self, job):
        jobfunc = job.__dict__['job_func']
        if len(jobfunc.args) >= 1:
            return jobfunc.args[0]
        else:  # pragma: no cover
            return jobfunc.keyworkds.get('jobId')

    def list_jobs(self):
        d = dict()
        for job in self.schedule.jobs:
            jobid = self.get_jobId(job)
            d[jobid] = job
        return d

    def shutdown(self):
        self.schedule.clear()

    def get_handlers(self, t):
        handle_list = []
        if t in self.handles:
            handle_list.append(self.handles[t])

        for helper in self.actions.itervalues():
            if t in helper.handles:
                handle_list.append(helper.handles[t])
        return handle_list

scheduler_interface = Scheduler()
