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
poseidonMain

Created on 29 May 2016
@author: dgrossman, lanhamt
"""
import json
import logging
import logging.config
import time
from os import getenv

from Investigator.Investigator import investigator_interface
from Scheduler.Scheduler import scheduler_interface

from Config.Config import config_interface


class PoseidonMain(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        self.shutdown = False

        self.mod_configuration = dict()

        self.mod_name = self.__class__.__name__
        self.config_section_name = self.mod_name

        self.Investigator = investigator_interface
        self.Investigator.set_owner(self)

        self.Scheduler = scheduler_interface
        self.Scheduler.set_owner(self)

        self.Config = config_interface
        self.Config.set_owner(self)

        self.Config.configure()
        self.Config.configure_endpoints()

        self.Investigator.configure()
        self.Investigator.configure_endpoints()

        self.Scheduler.configure()
        self.Scheduler.configure_endpoints()

        for item in self.Config.get_section(self.config_section_name):
            k, v = item
            self.mod_configuration[k] = v

        self.init_logging()

    def init_logging(self):
        config = None

        path = getenv('loggingFile', None)

        if path is None:
            path = self.mod_configuration.get('loggingFile', None)

        if path is not None:
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def handle(self, tv):
        t, v = tv
        if t == 'Main':
            if v == 'shutdown':
                self.shutdown = True

    def get_queue_item(self):
        return('t', 'v')

    def init_rabbit(self):
        pass

    def processQ(self):
        x = 10
        while not self.shutdown and x > 0:
            start = time.clock()
            time.sleep(1)

            x = x - 1

            # type , value
            t, v = self.get_queue_item()

            handle_list = self.Scheduler.get_handlers(t)
            if handle_list is not None:
                for handle in handle_list:
                    handle(v)
            handle_list = self.Investigator.get_handlers(t)
            if handle_list is not None:
                for handle in handle_list:
                    handle(v)

            elapsed = time.clock()
            elapsed = elapsed - start

            logLine = 'time to run eventloop is %0.3f ms' % (elapsed * 1000)
            self.logger.debug(logLine)
            print logLine


def main():
    pmain = PoseidonMain()
    pmain.init_rabbit()
    pmain.processQ()
    return True

if __name__ == '__main__':  # pragma: no cover
    main()
