#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon

Created on 3 December 2018
@author: Charlie Lewis
"""
import logging
import sys
import threading
import time
from functools import partial

import schedule
from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.controllers.sdnconnect import SDNConnect
from poseidon_core.controllers.sdnevents import SDNEvents
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.log import Logger
from poseidon_core.helpers.prometheus import Prometheus
from poseidon_core.operations.monitor import Monitor


def start_prometheus(logger):
    prom = Prometheus()
    try:
        prom.initialize_metrics()
    except Exception as e:  # pragma: no cover
        logger.debug(
            f'Prometheus metrics are already initialized: {e}')
    Prometheus.start()
    return prom


def schedule_thread_worker(logger, scheduler=schedule):
    ''' schedule thread, takes care of running processes in the future '''
    logger.debug('Starting thread_worker')
    while True:
        sys.stdout.flush()
        scheduler.run_pending()
        time.sleep(1)


def main():  # pragma: no cover
    logging.getLogger('pika').setLevel(logging.CRITICAL)
    Logger()
    logger = logging.getLogger('main')
    config = Config().get_config()
    prom = start_prometheus(logger)

    # TODO option that doesn't require an sdn connection?
    sdnc = SDNConnect(config=config, logger=logger, prom=prom,
                      faucetconfgetsetter_cl=FaucetRemoteConfGetSetter)

    sdne = SDNEvents(logger, prom, sdnc)
    sdne.start_message_queues()

    # TODO this should be the default operation, but can be overridden with config to do other operations instead or additionally
    monitor = Monitor(logger, config, schedule, sdne.job_queue, sdnc, prom)

    # schedule all threads
    schedule_thread = threading.Thread(
        target=partial(
            schedule_thread_worker,
            logger, scheduler=schedule),
        name='st_worker')
    schedule_thread.start()

    try:
        # TODO each operation should have its own thread running its own "process" and this is just a main infinite loop
        sdne.process(monitor)
    except Exception as e:
        logger.error(f'Something went wrong, restarting because: {e}')
        sys.exit(1)
