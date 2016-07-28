import collections

from enum import Enum


class EVERY(Enum):
    once = 0
    minute = 1
    hour = 60
    day = 3600

CRONSPEC = collections.namedtuple('CronSpec', ['occurs', 'starts'])
