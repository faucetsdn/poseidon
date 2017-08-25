#!/usr/bin/python
import ast

import nfilter
import pytest
import web
from paste.fixture import TestApp


def start_web_app():
    """ starts the web app in a TestApp for testing """
    nf_inst = nfilter.NFilter()
    urls = nf_inst.urls()
    app = web.application(urls, globals())
    testApp = TestApp(app.wsgifunc())
    return testApp


def test_start_r():
    """ tests the restful endpoint: start """
    # get web app
    testApp = start_web_app()

    # test start
    r = testApp.get('/start/foo')
    assert r.status == 200


def test_stop_r():
    """ tests the restful endpoint: stop """
    # get web app
    testApp = start_web_app()

    # test stop
    r = testApp.get('/stop/foo')
    assert r.status == 200


def test_create_r():
    """ tests the restful endpoint: create """
    # get web app
    testApp = start_web_app()

    # test create
    r = testApp.post(
        '/create',
        params={
            'id': 'foo',
            'interval': '60',
            'filter': '',
            'nic': 'eth1'},
        headers={
            'Content-Type': 'application/json'})
    assert r.status == 200
    r = testApp.post('/create', params={})
    assert r.status == 200
    r = testApp.post('/create', params={'nic': 'eth1'})
    assert r.status == 200
    r = testApp.post('/create', params={'nic': 'eth1', 'id': 'foo'})
    assert r.status == 200
    r = testApp.post(
        '/create', params={'nic': 'eth1', 'id': 'foo', 'interval': '60'})
    assert r.status == 200
    r = testApp.post('/create', params='{}')
    assert r.status == 200


def test_filters_r():
    """ tests the restful endpoint: filters """
    # get web app
    testApp = start_web_app()

    # test filters
    r = testApp.get('/filters')
    assert r.status == 200
