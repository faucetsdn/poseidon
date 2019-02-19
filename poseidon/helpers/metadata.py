# -*- coding: utf-8 -*-
"""
Created on 19 February 2019
@author: Charlie Lewis
"""
import socket


def get_ether_vendor(mac, lookup_path):
    """
    Takes a MAC address and looks up and returns the vendor for it.
    """
    vendor = 'UNDEFINED'
    mac = ''.join(mac.split(':'))[:6].upper()
    with open(lookup_path, 'r') as f:
        for line in f:
            if line.startswith(mac):
                return line.split()[1].strip()
    return vendor


def get_rdns_lookup(ip):
    """
    Takes an IP address adn looks up what the reverse DNS is if it exists.
    """
    socket.settimeout(1.0)
    try:
        rdns = socket.gethostbyaddr(ip)[0]
    except Exception as e:  # pragma: no cover
        rdns = 'UNDEFINED'
    return rdns
