#!/bin/bash

NIC="$1"
INTERVAL="$2"
ID="$3"
FILTER="$4"
ITERS="$5"

# if ITERS is non-negative then do the capture ITERS times
if [ $ITERS -gt "0" ]; then
    COUNTER=0
    while [ $COUNTER -lt $ITERS ]; do
        tcpdump -ni $NIC -s65535 -G $INTERVAL -w 'trace_'"$ID"'_%Y-%m-%d_%H:%M:%S.pcap' -W 1 $FILTER;
        mv *.pcap /files/;
        let COUNTER=COUNTER+1;
    done
else  # else do the capture until killed
    while true
    do
        tcpdump -ni $NIC -s65535 -G $INTERVAL -w 'trace_'"$ID"'_%Y-%m-%d_%H:%M:%S.pcap' -W 1 $FILTER;
        mv *.pcap /files/;
    done
fi