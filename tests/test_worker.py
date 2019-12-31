# -*- coding: utf-8 -*-
"""
Created on 31 Dec 2019
@author: cglewis
"""
from workers.worker import callback
from workers.worker import load_workers
from workers.worker import main
from workers.worker import setup_docker
from workers.worker import setup_redis


def test_setup_docker():
    d = setup_docker()


def test_load_workers():
    os.system('cp workers/workers.json workers.json')
    workers = load_workers()
