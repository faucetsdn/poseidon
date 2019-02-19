# -*- coding: utf-8 -*-
"""
Created on 19 February 2019
@author: Charlie Lewis
"""


def get_ether_vendor(mac, lookup_path):
    """
    Takes a MAC address and looks up and returns the vendor for it.
    """
    vendor = 'UNDEFINED'
    mac = ''.join(mac.split(':'))[:6]
    with open(lookup_path, 'r') as f:
        for line in f:
            if line.startswith(mac):
                vendor = line.split()[1].strip()
    return vendor
