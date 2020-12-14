#!/bin/bash

set -e

POSEIDON_IMAGE=$(grep -Eo "image:.+poseidon:[^\']+" docker-compose.yaml |grep -Eo ':\S+')
if [[ "$POSEIDON_IMAGE" == "" ]] ; then
        echo error: cannot detect poseidon docker image name.
        exit 1
fi
if [[ "$POSEIDON_IMAGE" != ":latest" ]] ; then
        echo poseidon image is $POSEIDON_IMAGE, so not running e2e tests  - assuming release
        exit 0
fi

TMPDIR=$(mktemp -d)

FASTREPLAY="sudo tcpreplay -q -t -i sw1b $TMPDIR/test.pcap"
SLOWREPLAY="sudo tcpreplay -q -M5 -i sw1b $TMPDIR/test.pcap"

wait_var_nonzero () {
        var=$1
        cmd=$2
        failvar=$3
        api="http://0.0.0.0:9090/api/v1/query?query="
        query="$api$var>0"
        echo waiting for $query to be non-zero
        RC="[]"
        TRIES=0
        while [[ "$RC" == "[]" ]] || [[ $RC == "" ]] ; do
                RC=$(echo "$query" | wget -q -O- -i -|jq .data.result)
                TRIES=$((TRIES+1))
                if [[ "$TRIES" == "180" ]] ; then
                        echo FAIL: $query returned no results: $RC
                        echo diagnostic logs follow
                        if [[ "$failvar" != "" ]] ; then
                                echo "$api$failvar" | wget -q -O- -i -
                        fi
                        grep -v store /var/log/poseidon/poseidon.log |tail -500
                        docker ps -a
                        echo FAIL: $query returned no results: $RC
                        exit 1
                fi
                if [[ "$cmd" == "" ]] ; then
                        sleep 1
                else
                        echo $($cmd)
                fi
        done
        echo $RC
}

wait_job_up () {
        instance=$1
        wait_var_nonzero "up{instance=\"$instance\"}" "" up
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

# pre-fetch workers to avoid timeout.
for i in $(jq < workers/workers.json '.workers[] | .image + ":" + .version' | sed 's/"//g') ; do
        docker pull $i
done

COMPOSE_PROJECT_NAME=ovs docker-compose -f tests/test-e2e-ovs.yml down
COMPOSE_PROJECT_NAME=ovs docker-compose -f tests/test-e2e-ovs.yml rm -f
COMPOSE_PROJECT_NAME=ovs docker-compose -f tests/test-e2e-ovs.yml up -d
OVSID="$(docker ps -q --filter name=ovs)"
while ! docker exec -t $OVSID ovs-vsctl show ; do
        echo waiting for OVS
        sleep 1
done
sudo sudo ip link add sw1a type veth peer name sw1b && true
sudo sudo ip link add mirrora type veth peer name mirrorb && true
docker exec -t $OVSID ovs-vsctl add-br switch1  -- set bridge switch1 other-config:datapath-id=0x1 -- set bridge switch1 datapath_type=netdev
docker exec -t $OVSID ovs-vsctl add-port switch1 sw1a -- set interface sw1a ofport_request=1
docker exec -t $OVSID ovs-vsctl add-port switch1 mirrora -- set interface mirrora ofport_request=3
docker exec -t $OVSID ovs-vsctl set-controller switch1 tcp:127.0.0.1:6653 tcp:127.0.0.1:6654
docker exec -t $OVSID ovs-vsctl show
docker exec -t $OVSID ovs-ofctl dump-ports switch1
for i in mirrora mirrorb switch1 sw1a sw1b ; do
        sudo /sbin/sysctl net.ipv6.conf.$i.disable_ipv6=1
        sudo ip link set $i down
done
for i in mirrora mirrorb switch1 ; do
        sudo ip link set $i up
done
export POSEIDON_PREFIX=/
export PATH=bin:$PATH
sudo rm -rf /opt/poseidon* /var/log/poseidon*
tar cvf $TMPDIR/current.tar .
poseidon -i $TMPDIR/current.tar
sudo sed -i -E \
  -e "s/logger_level.+/logger_level = DEBUG/;" \
  -e "s/collector_nic.+/collector_nic = mirrorb/;" \
  -e "s/reinvestigation_frequency.+/reinvestigation_frequency = 60/" \
  -e "s/max_concurrent_reinvestigations.+/max_concurrent_reinvestigations = 1/" \
  /opt/poseidon/poseidon.config
sudo cat /opt/poseidon/poseidon.config
wget https://github.com/IQTLabs/NetworkML/raw/master/tests/test_data/trace_ab12_2001-01-01_02_03-client-ip-1-2-3-4.pcap -O$TMPDIR/test.pcap
poseidon -s
wait_job_up faucetconfrpc:59998
wait_job_up faucet:9302
wait_var_nonzero "port_status{port=\"3\"}" "" port_status
wait_job_up gauge:9303
wait_var_nonzero "dp_status{dp_name=\"switch1\"}" "" dp_status
wait_job_up poseidon:9304
for i in sw1a sw1b ; do
        sudo ip link set $i up
done
wait_var_nonzero "port_status{port=\"1\"}" "" port_status
echo waiting for FAUCET to recognize test port
COUNT="0"
while [[ "$COUNT" == 0 ]] ; do
        COUNT=$(docker exec -t $OVSID ovs-ofctl dump-flows -OOpenFlow13 switch1 table=0,in_port=1|grep -c in_port|cat)
        sleep 1
done
# Poseidon event client receiving from FAUCET
wait_var_nonzero "poseidon_last_rabbitmq_routing_key_time{routing_key=\"FAUCET.Event\"}" "" poseidon_last_rabbitmq_routing_key_time
# Poseidon detected endpoints
wait_var_nonzero "sum(poseidon_endpoint_current_states{current_state=\"mirroring\"})" "$FASTREPLAY" poseidon_endpoint_current_states
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
echo $($SLOWREPLAY)
# wait for networkml to return a result
wait_var_nonzero "poseidon_last_rabbitmq_routing_key_time{routing_key=\"poseidon.algos.decider\"}" "" poseidon_last_rabbitmq_routing_key_time
# keep endpoints active awaiting results
wait_var_nonzero "sum(poseidon_endpoint_roles{role!=\"NO DATA\"})" "$FASTREPLAY" poseidon_endpoint_roles
# p0f doesn't always return a decision - but check that it returned
# TODO: determine why p0f not deterministic.
wait_var_nonzero "sum(poseidon_endpoint_oses)" "" poseidon_endpoint_oses
# TODO: fix certstrap to allow creating multiple named client keys.
wait_var_nonzero "sum(faucetconfrpc_ok_total{peer_id=\"poseidon\"})" "" faucetconfrpc_ok_total
for rpc in GetConfigFile SetConfigFile ClearPortMirror AddPortMirror RemovePortMirror ; do
        wait_var_nonzero "faucetconfrpc_ok_total{peer_id=\"poseidon\",request=\"$rpc\"}" "" faucetconfrpc_ok_total
done
poseidon -S
poseidon -d
COMPOSE_PROJECT_NAME=ovs docker-compose -f tests/test-e2e-ovs.yml stop
rm -rf $TMPDIR
