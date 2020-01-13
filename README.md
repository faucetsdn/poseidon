# Poseidon

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://travis-ci.org/CyberReboot/poseidon.svg?branch=master)](https://travis-ci.org/CyberReboot/poseidon)
[![codecov](https://codecov.io/gh/CyberReboot/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/CyberReboot/poseidon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e31df16fa65447bf8527e366c6271bf3)](https://www.codacy.com/app/CyberReboot/poseidon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CyberReboot/poseidon&amp;utm_campaign=Badge_Grade)
[![Docker Hub Downloads](https://img.shields.io/docker/pulls/cyberreboot/poseidon.svg)](https://hub.docker.com/r/cyberreboot/poseidon/)

> Software Defined Network Situational Awareness

<img src="/docs/img/poseidon-logo.png" width="67" height="93" hspace="20"/><a href="https://web.archive.org/web/20170316012151/https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/img/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year" hspace="20"></a>

Poseidon began as a joint effort between two of the IQT Labs: [Cyber Reboot](https://www.cyberreboot.org/) and [Lab41](http://www.lab41.org/). The project's goal is to explore approaches to better identify what nodes are on a given (computer) network and understand what they are doing.  The project utilizes Software Defined Networking and machine learning to automatically capture network traffic, extract relevant features from that traffic, perform classifications through trained models, convey results, and provide mechanisms to take further action. While the project works best leveraging modern SDNs, parts of it can still be used with little more than packet capture (pcap) files.

## Table of Contents

- [Background](#background)
- [Prerequisites](#prerequisites)
- [Installing Poseidon](#installing)
- [SDN Controller Configuration](#sdn-controller-configuration)
    - [Faucet Configuration](#faucet-configuration)
    - [Big Cloud Fabric Configuration](#big-cloud-fabric-configuration)
      - [Span Fabric](#span-fabric)
      - [Interface Group](#interface-group)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Network Data Logging](#logging)
- [Related Components](#related-components)
- [Additional Info](#additional-info)

## Background

The Poseidon project originally began as an experiment to test the merits of leveraging SDN and machine learning techniques to detect abnormal network behavior. (Please read our [blogs posts](#additional-info) linked below for several years of background) While that long-term goal remains, the unfortunate reality is that the state of rich, labelled, public, and MODERN network data sets for ML training is pretty poor. Our lab is working on improving the availability of network training sets, but in the near term the project remains focused on 1) improving the accuracy of identifying what a node *IS* (based on captured IP header data) and 2) developing Poseidon into a "harness" of sorts to house machine learning techniques for additional use cases. (Read: Not just ours!)


## Prerequisites

- [Docker](https://www.docker.com/) - Poseidon and related components run on top of Docker, so understanding the fundamentals will be useful for troubleshooting as well.  Note: installing via Snap is currently unsupported. [A Good Ubuntu Docker Quick-Start](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04)
- [Compose](https://docs.docker.com/compose/) - Poseidon is orchestrated with [docker-compose](https://docs.docker.com/compose/install/). You will need a version that supports compose file format version 3.
- [Curl](https://curl.haxx.se/download.html) - command-line for transferring data with URLs.
- [jq](https://stedolan.github.io/jq/download/) - command-line JSON processor.
- An SDN Controller - specifically [BigSwitch Cloud Fabric](https://www.bigswitch.com/community-edition) or [Faucet](https://faucet.nz/)
- ~10GB of free disk space

> Note: Installation on `OS X` is possible but not supported.

## Installing

### Permissions for Docker

To simplify using commands with Docker, we recommend allowing the user that will be executing Poseidon commands be part of the `docker` group so they can execute Docker commands without `sudo`.  Typically, this can be done with:
```
sudo usermod -aG docker $USER
```
Followed by closing the existing shell and starting a new one.

### Getting the bits

```
curl -L https://raw.githubusercontent.com/CyberReboot/poseidon/master/bin/poseidon -o /usr/local/bin/poseidon
chmod +x /usr/local/bin/poseidon
```

## SDN Controller Configuration
You need to first identify one of the two supported controllers (*BigSwitch Cloud Fabric* or *Faucet*). The controller needs to be running and accessible (via network API) by the Poseidon system.  We recommend making sure the SDN portion is configured BEFORE the above Poseidon installation, but it's not a hard requirement.

#### Faucet Configuration
<img src="/docs/img/faucet.png" width="190" height="100">
Poseidon requires at least Faucet version 1.8.6 or higher.

Unless Poseidon and Faucet are running on the same host, Poseidon will connect to Faucet using SSH.  So you'll need to create an account that can SSH to the machine running Faucet and that has rights to modify the configuration file `faucet.yaml` (currently Poseidon expects it to be in the default `/etc/faucet/faucet.yaml` location and `dps` must all be defined in `faucet.yaml` for Poseidon to update the network posture correctly).

If you have Faucet running already, make use Faucet is started with the following environment variables, which allow Poseidon to change its config, and receive Faucet events:

```
export FAUCET_EVENT_SOCK=1
export FAUCET_CONFIG_STAT_RELOAD=1
```

Faucet is now configured and ready for use with Poseidon.

#### BigSwitch Big Cloud Fabric Configuration
<img src="/docs/img/bcf.png" width="114" height="100"/>
You will need to access the API of your Big Cloud Fabric (BCF) controller using authorized credentials (user/pass) and you will need to add support in your BCF controller for moving mirrored endpoint network data around your network. In BCF, allowing port mirroring for Poseidon is done using 1) the "span-fabric" feature and 2) identifying a switch interface to send the captured ("spanned") traffic out of. The BigSwitch config will need an admin to add:


- span-fabric: you need to define a fabric-wide port mirroring mechanism and give it a name (e.g. 'poseidon')
- interface-group: you need to identify which port the mirrored traffic is going to egress from, and name it (e.g. 'ig1')

##### Span Fabric

Replace `<name>` with the name of your span-fabric and `<interface-group>` with the name of your interface-group.
```
! span-fabric
span-fabric <name>
  active
  destination interface-group <interface-group>
  priority 1
```

##### Interface Group

Replace `<interface-group>` with the name of your interface-group. Additionally fill in the `YOUR_LEAF_SWITCH` and `YOUR_INTERFACE_WHERE_VENT_WILL_RECORD_TRAFFIC_FROM`.
```
! interface-group
interface-group <interface-group>
  description 'packets get mirrored here to be processed'
  mode span-fabric
  member switch YOUR_LEAF_SWITCH interface YOUR_INTERFACE_WHERE_VENT_WILL_RECORD_TRAFFIC_FROM
```

Poseidon will connect to the BCF controller using its REST API, so you will also need the BCF API hostname or IP address and credentials for the controller. If your controller is an HA pair and has a virtual IP address, we recommend using that virtual address. Also, because Poseidon will be making dynamic `filter` rule changes we will need an account that has administrative privileges.  (Poseidon only modifies the filter rules of the defined span-fabric, but until BigSwitch has more granular access control options this means admin privs!) Bringing the above configuration requirements together, below is an example of what the relevant parts of your BCF configuration could look like where the span-fabric is called 'poseidon', the user 'poseidon' is defined for API access, and the egress interface is interface '48' on switch 'leaf04' and labelled as interface group 'ig1':

```
! user
user poseidon
  hashed-password method=PBKDF2WithHmacSHA512,salt=M4534fcV1Ksg_fNm2pGQ,rounds=25000,ph=true,eWNHYUPVAUYosBVRguJnkmAzM

! group
group admin
  associate user poseidon

! interface-group
interface-group ig1
  description 'Mirroring for Poseidon'
  mode span-fabric
  member switch leaf04 interface ethernet48

! span-fabric
span-fabric poseidon
  active
  destination interface-group ig1
  priority 1
```

BCF is now configured and ready for use with Poseidon.

## Starting Poseidon

Poseidon supports an existing Faucet/Gauge, Prometheus/Grafana installation. Or, Poseidon can start all those tasks for you. If you have an existing Faucet/Gauge Prometheus/Gauge et al installation, you will need to integrate Poseidon's Prometheus and Grafana configuration with your existing installation manually. You won't need to do this right away, but until you do you won't be able to see Poseidon's Grafana based dashboards.

To start everything run:

```
docker-compose -f docker-compose.yaml -f helpers/faucet/docker-compose-experimental.yaml -f helpers/faucet/docker-compose-experimental-faucet.yaml -f helpers/faucet/docker-compose-experimental-monitoring.yaml up -d --build
```

If you run Faucet/Grafana and Prometheus/Grafana already, you can run:

```
docker-compose -f docker-compose.yaml -f helpers/faucet/docker-compose-experimental.yaml up -d --build
```

## Usage

After installation you'll have a new command `poseidon` available for looking at the configuration, logs, and shell, as well as stopping and starting the service.
```
$ poseidon help
Poseidon, an application that leverages software defined networks (SDN) to acquire and then feed network traffic to a number of machine learning techniques. For more info visit: https://github.com/CyberReboot/poseidon

Usage: poseidon [option]
Options:
    -a,  api           get url to the Poseidon API
    -c,  config        display current configuration info
    -d,  delete        delete Poseidon installation (uses sudo)
    -e,  shell         enter into the Poseidon shell, requires Poseidon to already be running
    -h,  help          print this help
    -i,  install       install Poseidon repo (uses sudo)
    -l,  logs          display the information logs about what Poseidon is doing
    -r,  restart       restart the Poseidon service (uses sudo)
    -s,  start         start the Poseidon service (uses sudo)
    -S,  stop          stop the Poseidon service (uses sudo)
    -u,  update        update Poseidon repo, optionally supply a version (uses sudo)
    -v,  viz/visualize get url to visualize Poseidon with CRviz
    -V,  version       get the version installed
```

Step 0:

Optionally specify a prefix location to install Poseidon by setting an environment variable, if it is unset, it will default to `/opt` and Poseidon. (If using Faucet, it will also override `/etc` locations to this prefix.)

```
export POSEIDON_PREFIX=/tmp
```

Step 1:

```
poseidon install
```

Step 2:

Configure Poseidon for your preferred settings. Open `/opt/poseidon/poseidon.config` (add the Poseidon prefix if you specified one).

If you're planning to use BCF, change values in the `Poseidon` and `Bcf` sections. If using Faucet, make sure to minimally change the `controller_mirror_ports` to match the switch name and port number of your mirror port.  Regardless of which controller you choose, you will need to update the `collector_nic` in the `vent` section to match the interface name of the NIC your mirror port is connected to.

Step 3:

If you want to Poseidon to spin up Faucet for you as well, simply run:
```
poseidon start
```

Otherwise, if using BCF or your own installation of Faucet (note you'll need to wire together the event socket and config reload options yourself if you go this path):
```
poseidon start --standalone
```

## Troubleshooting

Poseidon by its nature depends on other systems. The following are some common issues and troubleshooting steps.

### Poseidon doesn't detect any hosts.

The most common cause of this problem, with the FAUCET controller, is RabbitMQ connectivity.

* Check that the RabbitMQ event adapter (faucet/event-adapter-rabbitmq) is running and not restarting.

```
# docker ps|grep faucet/event-adapter-rabbitmq
4a7509829be0        faucet/event-adapter-rabbitmq           "/usr/local/bin/entr…"   3 days ago          Up 3 days
```

* Check that FAUCET.Event messages are being received by Poseidon.

This command reports the time that the most recent FAUCET.Event message was received by Poseidon.

If run repeatedly over a couple of minutes this timestamp should increase.

```
docker exec -it poseidon_poseidon_1 /bin/sh
/poseidon # wget -q -O- localhost:9304|grep -E ^last_rabbitmq_routing_key_time.+FAUCET.Event
last_rabbitmq_routing_key_time{routing_key="FAUCET.Event"} 1.5739482267393966e+09
/poseidon # wget -q -O- localhost:9304|grep -E ^last_rabbitmq_routing_key_time.+FAUCET.Event
last_rabbitmq_routing_key_time{routing_key="FAUCET.Event"} 1.5739487978768678e+09
/poseidon # exit
```

### Poseidon doesn't report any host roles.

* Check that the mirror interface is up and receiving packets (should be configured in `collector_nic`. The interface must be up before Posiedon starts.

```
# ifconfig enx0023559c2781
enx0023559c2781: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet6 fe80::223:55ff:fe9c:2781  prefixlen 64  scopeid 0x20<link>
        ether 00:23:55:9c:27:81  txqueuelen 1000  (Ethernet)
        RX packets 82979981  bytes 77510139268 (77.5 GB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 202  bytes 15932 (15.9 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

* Check that there is disk space available and pcaps are being accumulated in */opt/vent_files* (add `POSEIDON_PREFIX` in front if it was used.)

```
# find /opt/vent_files -type f -name \*pcap |head -5
/opt/vent_files/trace_d3f3217106acd75fe7b5c7069a84a227c9e48377_2019-11-15_03_10_41.pcap
/opt/vent_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-client-ip-216-58-196-147-192-168-254-254-216-58-196-147-vssmonitoring-frame-eth-ip-icmp.pcap
/opt/vent_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-miscellaneous-192-168-254-1-192-168-254-254-vssmonitoring-frame-eth-arp.pcap
/opt/vent_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-client-ip-192-168-254-254-192-168-254-254-74-125-200-189-udp-frame-eth-ip-wsshort-port-443.pcap
/opt/vent_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/servers/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-server-ip-74-125-68-188-192-168-254-254-74-125-68-188-frame-eth-ip-tcp-port-5228.pcap
```


## Developing

### Modifying Code that Runs in a Docker Container

If installed as described above, poseidon's codebase will be at `/opt/poseidon`.  At this location, make changes, then run `poseidon restart`.

## Network Data Logging

Poseidon logs some data about the network it monitors. Therefore it is important to secure Poseidon's own host (aside from logging, Poseidon can of course change FAUCET's network configuration).

There are two main types of logging at the lowest level. The first is FAUCET events - FAUCET generates an event when it learns on which port a host is present on the network, and the event includes source and destination Ethernet MAC and IP addresses (if present). For example:

```
2019-11-21 20:18:41,909 [DEBUG] faucet - got faucet message for l2_learn: {'version': 1, 'time': 1574367516.3555572, 'dp_id': 1, 'dp_name': 'x930', 'event_id': 172760, 'L2_LEARN': {'port_no': 22, 'previous_port_no': None, 'vid': 254, 'eth_src': '0e:00:00:00:00:99', 'eth_dst': '0e:00:00:00:00:01', 'eth_type': 2048, 'l3_src_ip': '192.168.254.3', 'l3_dst_ip': '192.168.254.254'}}
```

The second type of logging is host based pcap captures, with most of the application (L4) payload removed. Poseidon causes the `ncapture` component (https://github.com/CyberReboot/network-tools/tree/master/network_tap/ncapture) to capture traffic, which is logged in `/opt/vent_files`. These are used in turn to learn host roles, etc.


## Related Components

- [CRviz](https://github.com/CyberReboot/CRviz)
- [NetworkML](https://github.com/CyberReboot/NetworkML)
- [network-tools](https://github.com/CyberReboot/network-tools)

## Additional Info

- [Authors](AUTHORS)
- Blog posts:
  - [How to Install Poseidon and get it working with Faucet SDN](https://blog.cyberreboot.org/how-to-install-poseidon-and-get-it-working-with-faucet-sdn-c3cdeed1901f)
  - [Running Poseidon on a 100G Netowork](https://blog.cyberreboot.org/running-poseidon-on-a-100g-network-8def4dc8eecd)
  - [Using machine learning to classify devices on your network](https://blog.cyberreboot.org/using-machine-learning-to-classify-devices-on-your-network-e9bb98cbfdb6)
  - [CRviz: Initial Release](https://blog.cyberreboot.org/crviz-initial-release-45a3023e0e93)
  - [CRviz: Scalable design for network visualization](https://blog.cyberreboot.org/crviz-scalable-design-for-network-visualization-14689133fd91)
  - [A better way to visualize what’s on our networks?](https://blog.cyberreboot.org/a-better-way-to-visualize-whats-on-our-networks-4f87fd42da6)
  - [TCPDump, and the care and feeding of an intelligent SDN](https://blog.cyberreboot.org/tcpdump-and-the-care-and-feeding-of-an-intelligent-sdn-eca6e7506342)
  - [The Case for Detecting Lateral Movement](https://blog.cyberreboot.org/the-case-for-detecting-lateral-movement-2018ae631b04)
  - [Poseidon with FAUCET SDN Controller](https://blog.cyberreboot.org/poseidon-with-faucet-sdn-controller-b5e78e46660b)
  - [Building a Software-Defined Network with Raspberry Pis and a Zodiac FX switch](https://blog.cyberreboot.org/building-a-software-defined-network-with-raspberry-pis-and-a-zodiac-fx-switch-97184032cdc1)
  - [Thanks to FAUCET, Poseidon Now Supports Switches Running OpenFlow 1.3](https://blog.cyberreboot.org/thanks-to-faucet-poseidon-now-supports-switches-running-openflow-1-3-e5489f2bc1f5)
  - [Deep Session Learning for Cyber Security](https://blog.cyberreboot.org/deep-session-learning-for-cyber-security-e7c0f6804b81)
  - [Introducing Vent](https://blog.cyberreboot.org/introducing-vent-1d883727b624)
  - [SDN and the need for more (security) verbs](https://blog.cyberreboot.org/sdn-and-the-need-for-more-security-verbs-a6315935fca4)
- See the latest changes [here](CHANGELOG.md).
- [Code of Conduct](CODE_OF_CONDUCT.md)
- Want to contribute? Awesome! Issue a pull request or see more details [here](CONTRIBUTING.md).
- Developer Guide
- [License](LICENSE)
- [Maintainers](MAINTAINERS)
- [Releases](https://github.com/CyberReboot/poseidon/releases)
- [Tests](https://travis-ci.org/CyberReboot/poseidon)
- [Version](VERSION)
- Videos:
  - [Installing Poseidon and Faucet together](https://www.youtube.com/watch?v=Qst5oNs5uY0)
  - [Analyzing and Visualizing Networks: The Powerful Combination of Poseidon and CRviz](https://www.youtube.com/watch?v=mTe5ajQRNL0)
  - [Poseidon + Faucet SDN](https://www.youtube.com/watch?v=nOgWze_4HOU)
