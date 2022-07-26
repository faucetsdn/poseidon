# -*- coding: utf-8 -*-
"""
Created on 19 February 2019
@author: Charlie Lewis
"""
import functools
import socket
from concurrent.futures import ThreadPoolExecutor

from poseidon_core.constants import NO_DATA


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
    except Exception:  # pragma: no cover
        return NO_DATA


class DNSResolver:

    TIMEOUT = 5

    @staticmethod
    def _resolve_ip(ip):
        try:
            result = socket.getnameinfo((ip, 0), 0)[0]
            if result == ip:
                return NO_DATA
            return result
        except socket.gaierror:
            return NO_DATA

    def resolve_ips(self, ips):
        with ThreadPoolExecutor() as executor:
            return {ip: result for ip, result in zip(ips, executor.map(DNSResolver()._resolve_ip, list(ips)))}
