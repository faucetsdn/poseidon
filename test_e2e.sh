#!/bin/bash

set -e

TMPDIR=$(mktemp -d)

wait_var_nonzero () {
	var=$1
	query="http://0.0.0.0:9090/api/v1/query?query=$var>0"
	echo waiting for $query to be non-zero
        RC="[]"
        TRIES=0
        while [[ "$RC" == "[]" ]] || [[ $RC == "" ]] ; do
                RC=$(echo "$query" | wget -q -O- -i -|jq .data.result)
                sleep 1
                TRIES=$((TRIES+1))
                if [[ "$TRIES" == "120" ]] ; then
			echo $query timed out: $RC
                        exit 1
                fi
        done
}

wait_job_up () {
	instance=$1
	wait_var_nonzero "up{instance=\"$instance\"}"
}

# TODO: push test capture into switch1:1 to ensure networkml is called
sudo rm -rf /etc/faucet
sudo mkdir -p /etc/faucet
cat >$TMPDIR/faucet.yaml<<EOF
# compatible with default poseidon config.
dps:
  switch1:
    dp_id: 0x1
    hardware: Open vSwitch
    interfaces:
        1:
           native_vlan: 100
        3:
           output_only: true
EOF
sudo mv $TMPDIR/faucet.yaml /etc/faucet

COMPOSE_PROJECT_NAME=ovs docker-compose -f test-e2e-ovs.yml down
COMPOSE_PROJECT_NAME=ovs docker-compose -f test-e2e-ovs.yml rm -f
COMPOSE_PROJECT_NAME=ovs docker-compose -f test-e2e-ovs.yml up -d
OVSID="$(docker ps -q --filter name=ovs)"
while ! docker exec -t $OVSID ovs-vsctl show ; do
        echo waiting for OVS
        sleep 1
done
sudo sudo ip link add sw1a type veth peer name sw1b && true
sudo sudo ip link add mirrora type veth peer name mirrorb && true
sudo ip link set sw1a down
sudo ip link set sw1b down
sudo ip link set mirrora up
sudo ip link set mirrorb up
docker exec -t $OVSID ovs-vsctl add-br switch1  -- set bridge switch1 other-config:datapath-id=0x1
docker exec -t $OVSID ovs-vsctl add-port switch1 sw1a -- set interface sw1a ofport_request=1
docker exec -t $OVSID ovs-vsctl add-port switch1 mirrora -- set interface mirrora ofport_request=3
docker exec -t $OVSID ovs-vsctl set-controller switch1 tcp:127.0.0.1:6653 tcp:127.0.0.1:6654
docker exec -t $OVSID ovs-vsctl show
docker exec -t $OVSID ovs-ofctl dump-ports switch1
export POSEIDON_PREFIX=/
export PATH=bin:$PATH
sudo rm -rf /opt/poseidon* /var/log/poseidon* /opt/redis
tar cvf $TMPDIR/current.tar .
poseidon -i $TMPDIR/current.tar
sudo sed -i -E \
  -e "s/logger_level.+/logger_level = DEBUG/;" \
  -e "s/collector_nic.+/collector_nic = mirrorb/;" \
  -e "s/reinvestigation_frequency.+/reinvestigation_frequency = 30/" \
  /opt/poseidon/poseidon.config
sudo cat /opt/poseidon/poseidon.config
wget https://github.com/IQTLabs/NetworkML/raw/master/tests/test_data/trace_ab12_2001-01-01_02_03-client-ip-1-2-3-4.pcap -O$TMPDIR/test.pcap
poseidon -s
wait_job_up faucet:9302
wait_job_up gauge:9303
wait_var_nonzero "dp_status{dp_name=\"switch1\"}"
wait_job_up poseidon:9304
sudo ip link set sw1a up
sudo ip link set sw1b up
# Poseidon event client receiving from FAUCET
wait_var_nonzero "last_rabbitmq_routing_key_time{routing_key=\"FAUCET.Event\"}"
sudo tcpreplay -t -i sw1b $TMPDIR/test.pcap
# Poseidon detected endpoints
wait_var_nonzero "sum(poseidon_endpoint_current_states{current_state=\"mirroring\"})"
echo waiting for ncapture
COUNT="0"
while [[ "$COUNT" == "0" ]] ; do
	COUNT=$(docker ps -a --filter=status=running|grep -c ncapture|cat)
	sleep 1
done
echo waiting for FAUCET mirror to be applied
COUNT="0"
while [[ "$COUNT" == 0 ]] ; do
	COUNT=$(docker exec -t $OVSID ovs-ofctl dump-flows -OOpenFlow13 switch1 table=0,in_port=1|grep -c output:|cat)
	sleep 1
done
# Send mirror traffic
sudo tcpreplay -t -i sw1b $TMPDIR/test.pcap
# wait for networkml to return a result
wait_var_nonzero "last_rabbitmq_routing_key_time{routing_key=\"poseidon.algos.decider\"}"
wait_var_nonzero "sum(poseidon_endpoint_oses{ipv4_os=\"Windows\"})"
wait_var_nonzero "sum(poseidon_endpoint_roles{role!=\"NO DATA\"})"
poseidon -S
poseidon -d
COMPOSE_PROJECT_NAME=ovs docker-compose -f test-e2e-ovs.yml stop
rm -rf $TMPDIR
