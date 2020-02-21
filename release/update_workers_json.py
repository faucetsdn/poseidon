#!/usr/bin/env python3
# Generate diff for workers.json to update to latest releases.
import json
import sys
import urllib.request


WORKERS_JSON = '../workers/workers.json'
RELEASE_MAP = {
    'cyberreboot/pcap-to-node-pcap': 'cyberreboot/network-tools',
    'cyberreboot/tcprewrite-dot1q': 'cyberreboot/network-tools',
    'cyberreboot/networkml': 'cyberreboot/networkml',
    'cyberreboot/p0f': 'cyberreboot/network-tools',
}


changes = set()
workers = json.loads(open(WORKERS_JSON).read())
for worker in workers['workers']:
    repo = RELEASE_MAP.get(worker['image'], None)
    if repo is None:
        print('Unknown repo for %s' % worker['image'])
        sys.exit(-1)
    req = urllib.request.Request(
        url='https://api.github.com/repos/%s/releases/latest' % repo)
    res = urllib.request.urlopen(req, timeout=15)  # nosec
    latest_json = json.loads(res.read().decode('utf-8'))
    latest_name = latest_json['name']
    if latest_name != latest_json['name']:
        changes.add((repo, latest_json['name']))
        worker['version'] = latest_name

with open(WORKERS_JSON, 'w') as f:
    f.write(json.dumps(workers, indent=2, sort_keys=True))


if changes:
    print('Upgrade workers: ' + ', '.join('%s: %s' % (repo, version)
                                          for repo, version in changes))
