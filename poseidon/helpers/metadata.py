# -*- coding: utf-8 -*-
"""
Created on 19 February 2019
@author: Charlie Lewis
"""
import functools
import random
import socket
from concurrent.futures import ProcessPoolExecutor

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
    except Exception:  # pragma: no cover
        return NO_DATA


class DNSResolver:

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
        list_ips = list(ips)
        random.shuffle(list_ips)
        results = {}
        with ProcessPoolExecutor(max_workers=4) as executor:
            for ip, result in zip(list_ips, executor.map(self._resolve_ip, list_ips)):
                results[ip] = result
        return results
