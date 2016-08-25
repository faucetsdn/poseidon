#!/usr/bin/env python
import logging
import sys

import web
from rest.create import CreateR
from rest.filters import FiltersR
from rest.start import StartR
from rest.stop import StopR


module_logger = logging.getLogger(__name__)


class NFilterServer(object):
    """
    This class is responsible for initializing the urls and web server.
    """
    # need __new__ for tests, but fails to call __init__ when actually running
    def __new__(*args, **kw):
        if hasattr(sys, '_called_from_test'):
            module_logger.info("don't call __init__")
        else:  # pragma: no cover
            return object.__new__(*args, **kw)

    def __init__(self, port=8080, host='0.0.0.0'):  # pragma: no cover
        nf_inst = NFilter()
        urls = nf_inst.urls()
        app = web.application(urls, globals())
        web.httpserver.runsimple(app.wsgifunc(), (host, port))


class NFilter:
    """
    This class is for defining things needed to start up.
    """

    def urls(self):
        urls = (
            '/create', CreateR,
            '/filters', FiltersR,
            '/start/(.+)', StartR,
            '/stop/(.+)', StopR
        )
        return urls

if __name__ == '__main__':
    NFilterServer().app.run()
