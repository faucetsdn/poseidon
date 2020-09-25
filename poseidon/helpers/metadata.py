# -*- coding: utf-8 -*-
"""
Created on 19 February 2019
@author: Charlie Lewis
"""
import functools
import dns.resolver

from poseidon.constants import NO_DATA


@functools.lru_cache()
def get_ether_vendor(mac, lookup_path):
    """
    Takes a MAC address and looks up and returns the vendor for it.
    """
    mac = ''.join(mac.split(':'))[:6].upper()
    try:
        with open(lookup_path, 'r') as f:
            for line in f:
                if line.startswith(mac):
                    return line.split()[1].strip()
    except Exception as e:  # pragma: no cover
        return NO_DATA


def get_rdns_lookup(ip, timeout=5):
    """
    Takes an IP address adn looks up what the reverse DNS is if it exists.
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = resolver.lifetime
        return str(resolver.resolve_address(ip).canonical_name)
    except (AttributeError, dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.exception.Timeout):  # pragma: no cover
        return NO_DATA
