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
periodically

Created on 11 July 2016
@author: dgrossman

"""
import datetime
import logging
import os
import sys
import time
import urllib2

module_logger = logging.getLogger(__name__)


def makeCall(url):
    ostr = 'makeCall {0}'.format(datetime.datetime.now().ctime())
    module_logger.info(ostr)
    if url:  # pragma: no cover
        try:
            page = urllib2.urlopen(url)
            module_logger.info(page.readlines())
            ostr = 'wget {0}'.format(url)
            module_logger.info(ostr)
        except:
            ostr = 'Error contacting url: {0} retrying...'.format(url)
            module_logger.error(ostr)


def doSleep(t):
    if t <= 0:
        module_logger.error('Too fast')
        return False
    else:
        time.sleep(t)
        return True


def periodically(wait, repeats, url):
    loops = 0
    next_call = time.time()

    if repeats < 0:  # pragma: no cover
        while True:
            makeCall(url)
            next_call = next_call + wait
            doSleep(next_call - time.time())

    else:
        while loops < repeats:
            loops = loops + 1
            makeCall(url)
            next_call = next_call + wait
            doSleep(next_call - time.time())
    return loops


def main(argv):  # pragma: no cover
    try:
        url = os.environ['KICKURL']
    except KeyError:
        url = None
    if len(argv) == 2:
        wait = abs(float(argv[0]))
        repeats = int(argv[1])
        periodically(wait, repeats, url)
    else:
        wait = abs(float(argv[0]))
        repeats = int(argv[1])
        if len(argv) == 3:
            url = argv[2]
        periodically(wait, repeats, url)


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])
