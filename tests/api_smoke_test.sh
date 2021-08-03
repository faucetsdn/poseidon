#!/bin/sh

SCRIPTPATH=$(readlink -f "$0")
TESTDIR=$(dirname $SCRIPTPATH)
APIDIR=$(readlink -f $TESTDIR/../src/api)
pushd $APIDIR && python3 setup.py install && popd
PYTHONPATH=$APIDIR timeout -s2 5s poseidon-api
X=$?
if [ $X -eq 124 ] || [ $X -eq 0 ] ; then echo PASS ; exit 0 ; fi
echo FAIL: exit $X
exit 1
