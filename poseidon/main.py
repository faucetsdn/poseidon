#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The main entrypoint for Poseidon,

Created on 3 December 2018
@author: Charlie Lewis
"""
import logging
from poseidon.helpers.log import Logger
from poseidon.helpers.rabbit import Rabbit
from poseidon.monitor import Monitor

CTRL_C = dict()
CTRL_C['STOP'] = False


def main(skip_rabbit=False):  # pragma: no cover
    logging.getLogger('pika').setLevel(logging.WARNING)
    Logger()
    logger = logging.getLogger('main')
    pmain = Monitor(logger, CTRL_C)
    host = pmain.controller['FA_RABBIT_HOST']
    port = int(pmain.controller['FA_RABBIT_PORT'])
    queue_name = 'poseidon_main'

    if not skip_rabbit:
        rabbit = Rabbit()
        exchange = 'topic-poseidon-internal'
        binding_key = ['poseidon.algos.#', 'poseidon.action.#']
        retval = rabbit.make_rabbit_connection(
            host, port, exchange, queue_name, binding_key)
        pmain.rabbit_channel_local = retval[0]
        pmain.rabbit_channel_connection_local = retval[1]
        pmain.rabbit_thread = rabbit.start_channel(
            pmain.rabbit_channel_local,
            pmain.rabbit_callback,
            queue_name,
            pmain.m_queue)

    rabbit = Rabbit()
    exchange = pmain.controller['FA_RABBIT_EXCHANGE']
    binding_key = [pmain.controller['FA_RABBIT_ROUTING_KEY']+'.#']
    retval = rabbit.make_rabbit_connection(
        host, port, exchange, queue_name, binding_key)
    pmain.rabbit_channel_local = retval[0]
    pmain.rabbit_channel_connection_local_fa = retval[1]
    pmain.rabbit_thread = rabbit.start_channel(
        pmain.rabbit_channel_local,
        pmain.rabbit_callback,
        queue_name,
        pmain.m_queue)

    pmain.schedule_thread.start()

    # loop here until told not to
    try:
        pmain.process()
    except Exception as e:
        logger.error('process() exception: {0}'.format(str(e)))

    pmain.shutdown()


if __name__ == '__main__':  # pragma: no cover
    main(skip_rabbit=False)
