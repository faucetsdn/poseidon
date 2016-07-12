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
import json


class NorthBoundControllerAbstraction(object):
    """NorthBoundControllerAbstraction """

    def __init__(self):
        self.modName = 'NorthBoundControllerAbstraction'
        print 'init()' + self.modName

    def printSuper(self):
        print 'doing Something in the super'


class Nbca(NorthBoundControllerAbstraction):

    def __init__(self):
        self.modName = 'Nbca'
        print 'init()' + self.modName
        super(Nbca, self).__init__()
        self.action2 = None

    class action1(object):

        def __init__(self):
            self.modName = 'action1'
            print 'init()' + self.modName

        def something(self):
            super.printSuper(self)

        def on_get(self, req, resp, resource):

            resp.content_type = 'text/text'
            try:
                resp.body = self.modName + ' found: %s' % (resource)
            except:  # pragma: no cover
                pass


class otherClass(object):

    def __init__(self):
        self.modName = 'otherClass'
        print 'init()' + self.modName
        self.retval = {}
        self.times = 0

    def on_get(self, req, resp):
        """Haneles Get requests"""
        # TODO make calls to get switch state,
        # TODO compare to previous switch state
        # TODO schedule something to occur for updated flows
        self.retval['times'] = self.times
        # TODO change response to something reflecting success of traversal
        self.retval['resp'] = 'ok'
        self.times = self.times + 1
        resp.body = json.dumps(self.retval)

"""
    def __call__(self, *args, **kwargs):
        print "call occured"
        print args
        print kwargs
"""

a = Nbca()
a.action2 = otherClass()
