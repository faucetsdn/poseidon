#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon

Created on 3 December 2018
@author: Charlie Lewis
"""
import logging

from poseidon_core.controllers.faucet.config import FaucetRemoteConfGetSetter
from poseidon_core.controllers.sdnconnect import SDNConnect
from poseidon_core.helpers.config import Config
from poseidon_core.helpers.log import Logger
from poseidon_core.helpers.rabbit import Rabbit
from poseidon_core.operations.monitor import Monitor


def create_message_queues(host, port, exchange, binding_key, pmain):
    rabbit = Rabbit()
    rabbit.make_rabbit_connection(
        host, port, exchange, binding_key)
    rabbit.start_channel(
        pmain.rabbit_callback, pmain.m_queue)
    pmain.rabbits.append(rabbit)
    return pmain


def start_message_queues(config, pmain):
    host = config['FA_RABBIT_HOST']
    port = int(config['FA_RABBIT_PORT'])
    exchange = 'topic-poseidon-internal'
    binding_key = ['poseidon.algos.#', 'poseidon.action.#']
    pmain = create_message_queue(host, port, exchange, binding_key, pmain)
    exchange = config['FA_RABBIT_EXCHANGE']
    binding_key = [config['FA_RABBIT_ROUTING_KEY']+'.#']
    pmain = create_message_queue(host, port, exchange, binding_key, pmain)
    pmain.schedule_thread.start()
    return pmain


def main():  # pragma: no cover
    logging.getLogger('pika').setLevel(logging.WARNING)
    Logger()
    logger = logging.getLogger('main')
    config = Config().get_config()
    sdnc = SDNConnect(config=config, logger=logger,
                      faucetconfgetsetter_cl=FaucetRemoteConfGetSetter)
    pmain = Monitor(logger, config, sdnc=sdnc)
    pmain = start_message_queues(config, pmain)

    # loop here until told not to
    try:
        pmain.process()
    except Exception as e:
        logger.info('Waiting for connection to RabbitMQ...')
