#!/bin/sh

set -e

KEYDIR=$1
HOST=$2
CA=${HOST}-ca

if [ ! -d "$KEYDIR" ] ; then mkdir -p "$KEYDIR" ; fi
if [ -f "$KEYDIR/$CA.crt" ] ; then exit 0 ; fi

CS="certstrap --depot-path $KEYDIR"
$CS init --common-name "$CA" --passphrase ""
$CS request-cert --domain "$HOST" --common-name "$HOST" --passphrase ""
$CS sign "$HOST" --CA "$CA"
