import collections

from enum import Enum


class EVERY(Enum):
    ''' constants used for scheduling when things occur'''
    once = 0
    minute = 1
    hour = 60
    day = 3600

CRONSPEC = collections.namedtuple('CronSpec', ['occurs', 'starts'])
