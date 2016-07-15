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
from Config.Config import config_interface
from Investigator.Investigator import investigator_interface
from Scheduler.Scheduler import scheduler_interface


class PoseidonMain(object):

    def __init__(self):
        self.mod_name = self.__class__.__name__
        self.mod_configuration = None
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

        self.mod_configuration = self.Config.get_section(
            self.config_section_name)


def main():
    pmain = PoseidonMain()
    print 'main'
    return True

if __name__ == '__main__':  # pragma: no cover
    main()
