#!/usr/bin/env python3
# Generate diff for workers.json to update to latest releases.
import json
import sys
import urllib.request


WORKERS_JSON = '../workers/workers.json'
RELEASE_MAP = {
    'iqtlabs/pcap_to_node_pcap': 'iqtlabs/network-tools',
    'iqtlabs/tcprewrite_dot1q': 'iqtlabs/network-tools',
    'iqtlabs/networkml': 'iqtlabs/networkml',
    'iqtlabs/p0f': 'iqtlabs/network-tools',
    'iqtlabs/faucetconfrpc': 'iqtlabs/faucetconfrpc',
    'yeasy/simple-web': 'yeasy/simple-web',
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
    try:
        res = urllib.request.urlopen(req, timeout=15)  # nosec
    except urllib.error.HTTPError:
        print('no release for %s, skipping update' % worker['image'])
        continue
    latest_json = json.loads(res.read().decode('utf-8'))
    latest_version = latest_json['name']
    if worker['version'] != latest_version:
        changes.add((repo, latest_version))
        worker['version'] = latest_version

with open(WORKERS_JSON, 'w') as f:
    f.write(json.dumps(workers, indent=2, sort_keys=True))


if changes:
    print('Upgrade workers: ' + ', '.join('%s: %s' % (repo, version)
                                          for repo, version in changes))
