#!/bin/python
import random
import urllib2
from time import sleep

f = open('urlList', 'r')
lines = f.readlines()

sitelist = list()

for l in lines:
    sitelist.append(l.strip())

    while True:
        try:
            site = lines[random.randint(1, len(sitelist))].strip()
            req = urllib2.urlopen(site)
            the_page = req.readlines()
            print 'site : {0}'.format(the_page[:1])
        except Exception as ex:
            template = 'exception occured {0} args:{1!r}'.format(
                type(ex).__name__, ex.args)
            print template
            print 'failed to open {0}'.format(site)
    sleep(5)
