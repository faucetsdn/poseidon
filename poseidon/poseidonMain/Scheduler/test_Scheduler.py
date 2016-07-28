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
Test module for Onos.py

Created on 28 June 2016
@author: dgrossman
"""
import logging

import pytest
from Scheduler import Scheduler
from Scheduler import scheduler_interface

from poseidon.baseClasses.enums_tuples import CRONSPEC
from poseidon.baseClasses.enums_tuples import EVERY


def test_instantiation():
    Scheduler()


def test_add():

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    jobId = 'JOBID'
    jobId2 = 'JOBID2'

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.minute, None)
    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)
    s.add_job(jobId2, b, somefunc)

    s.schedule.run_all()

    assert len(s.schedule.jobs) == 2
    s.shutdown()


def test_remove():
    jobId = 'JOBID'
    jobId2 = 'JOBID2'

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.minute, None)
    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)
    s.add_job(jobId2, b, somefunc)

    s.schedule.run_all()

    assert len(s.schedule.jobs) == 2

    s.del_job(jobId)

    assert len(s.schedule.jobs) == 1

    s.del_job(jobId2)

    assert len(s.schedule.jobs) == 0
    s.shutdown()


def test_schedule_once():
    jobId = 'JOBID'

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.once, '10:30')
    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)

    assert len(s.schedule.jobs) == 1
    s.schedule.run_all()
    assert len(s.schedule.jobs) == 0
    s.shutdown()


def test_schedule_day():
    jobId = 'JOBID'
    jobId2 = 'JOBID2'

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.day, None)
    c = CRONSPEC(EVERY.day, '10:30')

    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)
    s.add_job(jobId2, c, somefunc)

    s.schedule.run_all()

    assert len(s.schedule.jobs) == 2

    s.del_job(jobId)

    assert len(s.schedule.jobs) == 1

    s.del_job(jobId2)

    assert len(s.schedule.jobs) == 0
    s.shutdown()


def test_schedule_hour():
    jobId = 'JOBID'
    jobId2 = 'JOBID2'

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.hour, None)
    c = CRONSPEC(EVERY.hour, ':30')

    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)
    s.add_job(jobId2, c, somefunc)

    s.schedule.run_all()

    assert len(s.schedule.jobs) == 2

    s.del_job(jobId)

    assert len(s.schedule.jobs) == 1

    s.del_job(jobId2)

    assert len(s.schedule.jobs) == 0


def test_schedule_minute():
    jobId = 'JOBID'
    jobId2 = 'JOBID2'

    def somefunc(jobId, logger):
        print 'someFunc:', jobId, logger
        return True

    s = scheduler_interface
    s.logger = logging.getLogger('testing')
    s.logger.setLevel(logging.DEBUG)

    b = CRONSPEC(EVERY.minute, None)
    c = CRONSPEC(EVERY.minute, 5)

    print 'cronspec:', b

    s.add_job(jobId, b, somefunc)
    s.add_job(jobId2, c, somefunc)

    s.schedule.run_all()

    assert len(s.schedule.jobs) == 2

    s.del_job(jobId)

    assert len(s.schedule.jobs) == 1

    s.del_job(jobId2)

    assert len(s.schedule.jobs) == 0
