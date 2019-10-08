#!/bin/sh

SCRIPTPATH=$(readlink -f "$0")
TESTDIR=`dirname $SCRIPTPATH`
APIDIR=`readlink -f $TESTDIR/../api`
PYTHONPATH=$APIDIR timeout -s2 5s gunicorn -b 127.0.0.1:8000 -k gevent -w 1 app.app
if [ $? -eq 124 ] ; then echo PASS ; exit 0 ; fi
echo FAIL
exit 1
