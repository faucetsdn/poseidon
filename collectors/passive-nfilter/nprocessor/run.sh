#!/bin/bash

NIC="$1"
INTERVAL="$2"
ID="$3"
FILTER="$4"

while true
do
    tcpdump -ni $NIC -s65535 -G $INTERVAL -w 'trace_'"$ID"'_%Y-%m-%d_%H:%M:%S.pcap' -W 1 $FILTER;
    mv *.pcap /files/;
done
