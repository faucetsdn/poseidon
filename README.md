# Poseidon

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![Build Status](https://github.com/IQTLabs/poseidon/workflows/test/badge.svg)
[![codecov](https://codecov.io/gh/IQTLabs/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/IQTLabs/poseidon)
[![Docker Hub Downloads](https://img.shields.io/docker/pulls/iqtlabs/poseidon.svg)](https://hub.docker.com/r/iqtlabs/poseidon/)

> Software Defined Network Situational Awareness

<img src="/docs/img/poseidon-logo.png" width="67" height="93" hspace="20"/><a href="https://web.archive.org/web/20170316012151/https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/img/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year" hspace="20"></a>

Poseidon began as a joint effort between two of the IQT Labs: [Cyber Reboot](https://www.cyberreboot.org/) and [Lab41](http://www.lab41.org/). The project's goal is to explore approaches to better identify what nodes are on a given (computer) network and understand what they are doing.  The project utilizes Software Defined Networking and machine learning to automatically capture network traffic, extract relevant features from that traffic, perform classifications through trained models, convey results, and provide mechanisms to take further action. While the project works best leveraging modern SDNs, parts of it can still be used with little more than packet capture (pcap) files.

## Table of Contents

- [Background](#background)
- [Prerequisites](#prerequisites)
- [Installing or updating Poseidon](#installing)
- [SDN Controller Configuration](#sdn-controller-configuration)
    - [Faucet Configuration](#faucet-configuration)
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
- [git](https://git-scm.com/downloads) - distributed version control system.
- [jq](https://stedolan.github.io/jq/download/) - command-line JSON processor.
- An SDN Controller - specifically [Faucet](https://faucet.nz/)
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

*NOTE: If you have previously installed Poseidon from a .deb package, please remove it first. Installation from .deb is no longer supported.*

Install the poseidon script which we will use to install and manage Poseidon.

```
curl -L https://raw.githubusercontent.com/IQTLabs/poseidon/master/bin/poseidon -o /usr/local/bin/poseidon
chmod +x /usr/local/bin/poseidon
```

#### Faucet Configuration
<img src="/docs/img/faucet.png" width="190" height="100">
NOTE: Poseidon requires at least Faucet version 1.9.46 or higher.

Poseidon uses a faucetconfrpc server, to maintain Faucet configuration. Poseidon starts its own server for you by default, and also by default Poseidon and Faucet have to be on the same machine. To run Faucet on a separate machine, you will need to start faucetconfrpc on that other machine, and update `faucetconfrpc_address` to point to where the faucetconfrpc is running. You may also need to update `faucetconfrpc_client`, if you are not using the provided automatically generated keys.

If you have Faucet running already, make sure Faucet is started with the following environment variables, which allow Poseidon to change its config, and receive Faucet events:

```
export FAUCET_EVENT_SOCK=1
export FAUCET_CONFIG_STAT_RELOAD=1
```

Faucet is now configured and ready for use with Poseidon.

##### Faucet stacking

Faucet supports stacking (distributed switching - multiple switches acting together as one).  Poseidon also supports this - Poseidon's mirroring interface should be connected to a port on the root switch.  You will need to allocate a port on each non-root switch also, and install a loopback plug (either Ethernet or fiber) in that port.  Poseidon will detect stacking and take care of the rest of the details (using Faucet's tunneling feature to move mirror packets from the non-root switches to the root switch's mirror port).  The only Poseidon config required is to add the dedicated port on each switch to the `controller_mirror_port` dictionary.

## Configuring Poseidon

You will need to create a directory and config file on the server where Poseidon will run.

```
sudo mkdir /opt/poseidon
sudo cp config/poseidon.config /opt/poseidon
```

Now, edit this file. You will need to set at minimum:

* controller_type, as appropriate to the controller you are running (see above).
* collector_nic: must be set to the interface name on the server, that is connected to the switch mirror port.
* controller_mirror_ports: must be set to the interface on the switch that will be used as the mirror port.

Optionally, you may also set controller_proxy_mirror_ports (for switches that don't have their own mirror ports, and can be mirrored with another switch).


## Updating Poseidon

From v0.10.0, you can update an existing Poseidon installation with `poseidon -u` (your configuration will be preserved). Updating from previous versions is not supported - please remove and reinstall as above. You can also give `poseidon -u` a specific git hash if you want to update to an unreleased version.


## Usage

After installation you'll have a new command `poseidon` available for looking at the configuration, logs, and shell, as well as stopping and starting the service.
```
$ poseidon help
Poseidon, an application that leverages software defined networks (SDN) to acquire and then feed network traffic to a number of machine learning techniques. For more info visit: https://github.com/IQTLabs/poseidon

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

For using Faucet, make sure to minimally change the `controller_mirror_ports` to match the switch name and port number of your mirror port.  You will also need to update the `collector_nic` in the `poseidon` section to match the interface name of the NIC your mirror port is connected to.

Step 3:

If you don't have Faucet already and/or you want to Poseidon to spin up Faucet for you as well, simply run the following command and you will be done:

```
poseidon start
```

Step 4:

If you are using your own installation of Faucet, you will need to enable communication between Poseidon and Faucet. Poseidon needs to change Faucet's configuration, and Faucet needs to send events to Poseidon. This configuration needs to be set with environment variables (see https://docs.faucet.nz/). For example, if running Faucet with Docker, you will need the following environment configuration in the `faucet` service in your docker-compose file:

```
        environment:
            FAUCET_CONFIG: '/etc/faucet/faucet.yaml'
            FAUCET_EVENT_SOCK: '/var/run/faucet/faucet.sock'
            FAUCET_CONFIG_STAT_RELOAD: '1'
```

If Faucet and Poseidon are running on the same machine, you can start Poseidon and you will be done:

```
poseidon start --standalone
```

Step 5:

If you are running Faucet and Poseidon on different machines, configuration is more complex (work to make this easier is ongoing): execute Step 4 first. Then you will need to run `event-adapter-rabbitmq` and `faucetconfrpc` services on the Faucet host, and change Poseidon's configuration to match.

First start all services from `helpers/faucet/docker-compose.yaml` on the Faucet host, using a Docker network that has network connectivity with your Poseidon host. Set `FA_RABBIT_HOST` to be the address of your Poseidon host. `faucet_certstrap` will generate keys in `/opt/faucetconfrpc` which will need to be copied to your Poseidon host. Then modify `faucetconfrpc_address` in `/opt/poseidon/config/poseidon.config` to point to your Faucet host.

You can now start Poseidon:

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
/poseidon # wget -q -O- localhost:9304|grep -E ^poseidon_last_rabbitmq_routing_key_time.+FAUCET.Event
poseidon_last_rabbitmq_routing_key_time{routing_key="FAUCET.Event"} 1.5739482267393966e+09
/poseidon # wget -q -O- localhost:9304|grep -E ^poseidon_last_rabbitmq_routing_key_time.+FAUCET.Event
poseidon_last_rabbitmq_routing_key_time{routing_key="FAUCET.Event"} 1.5739487978768678e+09
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

* Check that there is disk space available and pcaps are being accumulated in */opt/poseidon_files* (add `POSEIDON_PREFIX` in front if it was used.)

```
# find /opt/poseidon_files -type f -name \*pcap |head -5
/opt/poseidon_files/trace_d3f3217106acd75fe7b5c7069a84a227c9e48377_2019-11-15_03_10_41.pcap
/opt/poseidon_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-client-ip-216-58-196-147-192-168-254-254-216-58-196-147-vssmonitoring-frame-eth-ip-icmp.pcap
/opt/poseidon_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-miscellaneous-192-168-254-1-192-168-254-254-vssmonitoring-frame-eth-arp.pcap
/opt/poseidon_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/clients/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-client-ip-192-168-254-254-192-168-254-254-74-125-200-189-udp-frame-eth-ip-wsshort-port-443.pcap
/opt/poseidon_files/tcprewrite-dot1q-2019-11-15-06_26_48.529473-UTC/pcap-node-splitter-2019-11-15-06_26_50.192570-UTC/servers/trace_0a6ce9490c193b65c3cad51fffbadeaed4ed5fdd_2019-11-15_06_11_24-server-ip-74-125-68-188-192-168-254-254-74-125-68-188-frame-eth-ip-tcp-port-5228.pcap
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

The second type of logging is host based pcap captures, with most of the application (L4) payload removed. Poseidon causes the `ncapture` component (https://github.com/IQTLabs/network-tools/tree/master/network_tap/ncapture) to capture traffic, which is logged in `/opt/poseidon_files`. These are used in turn to learn host roles, etc.


## Related Components

- [CRviz](https://github.com/IQTLabs/CRviz)
- [NetworkML](https://github.com/IQTLabs/NetworkML)
- [network-tools](https://github.com/IQTLabs/network-tools)

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
- [Releases](https://github.com/IQTLabs/poseidon/releases)
- [Tests](https://github.com/IQTLabs/poseidon/actions)
- [Version](VERSION)
- Videos:
  - [Installing Poseidon and Faucet together](https://www.youtube.com/watch?v=Qst5oNs5uY0)
  - [Analyzing and Visualizing Networks: The Powerful Combination of Poseidon and CRviz](https://www.youtube.com/watch?v=mTe5ajQRNL0)
  - [Poseidon + Faucet SDN](https://www.youtube.com/watch?v=nOgWze_4HOU)
