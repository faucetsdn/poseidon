#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon

Created on 3 December 2018
@author: Charlie Lewis
"""
import logging

from poseidon_core.helpers.log import Logger
from poseidon_core.helpers.rabbit import Rabbit
from poseidon_core.monitor import Monitor

def main():  # pragma: no cover
    logging.getLogger('pika').setLevel(logging.WARNING)
    Logger()
    logger = logging.getLogger('main')
    pmain = Monitor(logger)
    host = pmain.controller['FA_RABBIT_HOST']
    port = int(pmain.controller['FA_RABBIT_PORT'])

    rabbit = Rabbit()
    exchange = 'topic-poseidon-internal'
    binding_key = ['poseidon.algos.#', 'poseidon.action.#']
    rabbit.make_rabbit_connection(
        host, port, exchange, binding_key)
    rabbit.start_channel(
        pmain.rabbit_callback, pmain.m_queue)
    pmain.rabbits.append(rabbit)

    rabbit = Rabbit()
    exchange = pmain.controller['FA_RABBIT_EXCHANGE']
    binding_key = [pmain.controller['FA_RABBIT_ROUTING_KEY']+'.#']
    rabbit.make_rabbit_connection(
        host, port, exchange, binding_key)
    rabbit.start_channel(
        pmain.rabbit_callback, pmain.m_queue)
    pmain.rabbits.append(rabbit)

    pmain.schedule_thread.start()

    # loop here until told not to
    try:
        pmain.process()
    except Exception as e:
        logger.info('Waiting for connection to RabbitMQ...')
