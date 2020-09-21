#!/bin/bash

set -e

sudo pip3 install docker-compose

# TODO: push test capture into switch1:1 to ensure networkml is called
sudo rm -rf /etc/faucet
sudo mkdir -p /etc/faucet
cat >/tmp/faucet.yaml<<EOF
# compatible with default poseidon config.
dps:
  switch1:
    dp_id: 0x999
    hardware: Open vSwitch
    interfaces:
        1:
           native_vlan: 100
        3:
           output_only: true
EOF
sudo mv /tmp/faucet.yaml /etc/faucet

docker-compose -f test-e2e-ovs.yml up -d
OVSID="$(docker ps -q --filter name=ovs)"
while ! docker exec -t $OVSID ovs-vsctl show ; do
        echo waiting for OVS
        sleep 1
done
docker exec -t $OVSID ovs-vsctl add-br switch1 
docker exec -t $OVSID ovs-vsctl set-controller switch1 tcp:127.0.0.1:6653,tcp:127.0.0.1:6654
export POSEIDON_PREFIX=/
export PATH=bin:$PATH
poseidon -i
poseidon -s
poseidon -a
# TODO: ensure test capture container is learned.
poseidon -e "show all"  "quit"
poseidon -S
poseidon -d
docker-compose -f test-e2e-ovs.yml stop
