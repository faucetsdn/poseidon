# -*- coding: utf-8 -*-
"""
Test module for jsonmixin.
@author: kylez
"""
import json
import os

from httmock import response

from poseidon.controllers.mixins.jsonmixin import JsonMixin

cur_dir = os.path.dirname(os.path.realpath(__file__))


def test_JsonMixin():
    """
    Tests JsonMixin
    """
    # Craft a JSON response object
    with open(os.path.join(cur_dir, 'sample_json.json')) as f:
        j = json.loads(f.read().replace('\n', ''))
    res = response(content=json.dumps(j), headers={
                   'content-type': 'application/json'})

    # Parse the JSON response object
    parsed = JsonMixin.parse_json(res)
    assert parsed


def test_empty():
    # Verify that blank text fields are parsed properly.
    def obj(): return True  # Just a proxy object for attaching text field.
    obj.text = ''
    obj.status_code = 200
    obj.url = ''

    # see if this forces coverge of obj
    assert obj()

    parsed = JsonMixin.parse_json(obj)
    assert parsed == {}
