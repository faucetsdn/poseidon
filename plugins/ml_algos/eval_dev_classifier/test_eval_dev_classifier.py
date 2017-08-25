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
import sys
import os

from eval_dev_classifier import get_path
from eval_dev_classifier import get_host


def test_get_path():
    get_path()
    sys.argv = []
    get_path()


def test_get_host():
    get_host()
    os.environ['POSEIDON_HOST'] = '1.1.1.1'
    assert get_host() == '1.1.1.1'
