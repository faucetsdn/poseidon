# Poseidon

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://travis-ci.org/CyberReboot/poseidon.svg?branch=master)](https://travis-ci.org/CyberReboot/poseidon)
[![codecov](https://codecov.io/gh/CyberReboot/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/CyberReboot/poseidon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e31df16fa65447bf8527e366c6271bf3)](https://www.codacy.com/app/CyberReboot/poseidon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CyberReboot/poseidon&amp;utm_campaign=Badge_Grade)
[![Docker Hub Downloads](https://img.shields.io/docker/pulls/cyberreboot/poseidon.svg)](https://hub.docker.com/r/cyberreboot/poseidon/)

> Software Defined Network Situational Awareness

<img src="/docs/img/poseidon-logo.png" width="50" height="75"/><a href="https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/img/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year"></a>

Poseidon is a joint effort between two of the IQT Labs: [Cyber Reboot](https://www.cyberreboot.org/) and [Lab41](http://www.lab41.org/). The project's goal is to explore approaches to better identify what nodes are on a given (computer) network and understand what they are doing.  The project utilizes Software Defined Networking and machine learning to automatically capture network traffic, extract relevant features from that traffic, perform classifications through trained models, convey results, and provide mechanisms to take further action. While the project works best leveraging modern SDNs, parts of it can still be used with little more than packet capture (pcap) files.

## Table of Contents

- [Background](#background)
- [Prerequisites](#prerequisites)
- [Installing Poseidon](#installing)
- [SDN Controller Configuration](#sdn-controller-configuration)
    - [Big Cloud Fabric Configuration](#big-cloud-fabric-configuration)
      - [Span Fabric](#span-fabric)
      - [Interface Group](#interface-group)
    - [Faucet Configuration](#faucet-configuration)
- [Usage](#usage)
- [Related Components](#related-components)
- [Additional Info](#additional-info)

## Background

The Poseidon project originally began as an experiment to test the merits of leveraging SDN and machine learning techniques to detect abnormal network behavior. (Please read our [blogs posts](#additional-info) linked below for several years of background) While that long-term goal remains, the unfortunate reality is that the state of rich, labelled, public, and MODERN network data sets for ML training is pretty poor. Our lab is working on improving the availability of network training sets, but in the near term the project remains focused on 1) improving the accuracy of identifying what a node *IS* (based on captured IP header data) and 2) developing Poseidon into a "harness" of sorts to house machine learning techniques for additional use cases. (Read: Not just ours!)


## Prerequisites

- A dedicated Linux System or Virtual Machine (A Debian-based distribution is preferred - Ubuntu 16.x is ideal)
  - Currently supported versions for the .DEB install are:
    - Ubuntu 14.04
    - Ubuntu 16.04
    - Ubuntu 17.10
    - Ubuntu 18.04
- [Docker](https://www.docker.com/) - Poseidon and related components run on top of Docker, so understanding the fundamentals will be useful for troubleshooting as well. [A Good Ubuntu Docker Quick-Start](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04)
- ~10GB of free disk space
- An SDN Controller - specifically [BigSwitch Cloud Fabric](https://www.bigswitch.com/community-edition) or [Faucet](https://faucet.nz/) - if you want full functionality.

> Note: Installation on `OS X` is possible but not supported, see the `./helpers/run` file (above) as a starting point.

## Installing

On Ubuntu, this will download and install our `.deb` package from [Cloudsmith](https://cloudsmith.io/package/ns/cyberreboot/repos/poseidon/packages/).
```
sudo usermod -aG docker $USER
sudo apt-get install -y apt-transport-https curl
curl -sLf "https://dl.cloudsmith.io/public/cyberreboot/poseidon/cfg/gpg/gpg.F9E23875C98A1F72.key" | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://dl.cloudsmith.io/public/cyberreboot/poseidon/deb/ubuntu $(lsb_release -cs) main"
sudo apt-get update
sudo apt-get install poseidon
```

Note: The installer has a `Demo` option in the installation wizard that will deploy and configure the full Poseidon package, the Faucet SDN contoller (and related components like Grafana and Prometheus), mininet, and openvswitch.  We suggest the demo install as a starting point if much of this is new to you.


## SDN Controller Configuration
If you opt to do a full install (NOT the demo mode), you need to first identify one of the two supported controllers (*BigSwitch Cloud Fabric* or *Faucet*). The controller needs to be running and accessible (via network API) by the Poseidon system.  We recommend making sure the SDN portion is configured BEFORE the above Poseidon installation, but it's not a hard requirement.

#### Big Cloud Fabric Configuration
<img src="/docs/img/bcf.png" width="114" height="100"/>
You will need to add support for moving arbitrary endpoint network data around your network.  The BigSwitch config will need an admin to add:

- span-fabric
- interface-group

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

Poseidon will connect to BCF controller using its REST API, so you'll need the BCF API IP address and credentials to it.

BCF is now configured and ready for use with Poseidon.

#### Faucet Configuration
<img src="/docs/img/faucet.png" width="190" height="100">
Poseidon requires at least Faucet version 1.8.6 or higher.

Unless Poseidon and Faucet are running on the same host, Poseidon will connect to Faucet using SSH.  So you'll need to create an account that can SSH to the machine running Faucet and that has rights to modify the configuration file `faucet.yaml` (currently Poseidon expects it to be in the default `/etc/faucet/faucet.yaml` location and `dps` must all be defined in `faucet.yaml` for Poseidon to update the network posture correctly).

Faucet needs to be started with the following environment variables set:
```
export FAUCET_EVENT_SOCK=1
export FAUCET_CONFIG_STAT_RELOAD=1
```

If using the [RabbitMQ adapter for Faucet](https://github.com/faucetsdn/faucet/tree/master/adapters/vendors/rabbitmq) (recommended) make sure to also export `FA_RABBIT_HOST` to the IP address of the host where Poseidon is running.

Faucet is now configured and ready for use with Poseidon.

## Usage

NEW: If you have used the .DEB installer previously, it is worth noting that Poseidon is now packaged as a standard Linux service, and ties in nicely to both systemctl and journalctl.

After installation you'll have a new command `poseidon` available for looking at the status, logs, changing the configuration, or stopping and starting the service.
```
$ poseidon help
Poseidon 0.3.6, an application that leverages software defined networks (SDN) to acquire and then feed network traffic to a number of machine learning techniques. For more info visit: https://github.com/CyberReboot/poseidon

Usage: poseidon [option]
Options:
    -c,  config        display current configuration info
    -h,  help          print this help
    -i,  info/status   display current status of the Poseidon service
    -l,  logs          display the information logs about what Poseidon is doing
    -L,  system-logs   display the system logs related to Poseidon
    -R,  reconfig      reconfigures all settings (uses sudo, will restart the Poseidon service)
    -r,  restart       restart the Poseidon service (uses sudo)
    -s,  start         start the Poseidon service (uses sudo)
    -S,  stop          stop the Poseidon service (uses sudo)
    -v,  viz/visualize get url to visualize Poseidon with CRviz
    -V,  version       display the version of Poseidon and exit
    -Z,  reset         reset the configuration (uses sudo)

```

Poseidon makes heavy use of a sister project, [vent](https://vent.readthedocs.io/en/latest/?badge=latest). With a successful installation you should minimally see a combination of Poseidon and Vent components, to include:

1. The following 14 containers with a "(healthy)" STATUS listed (NOTE: this is truncated output):
```
# docker ps
CONTAINER ID        IMAGE                                  COMMAND                  STATUS  
8c07adf421fb        cyberreboot/poseidon:master            "/bin/sh -c '(flask …"   Up 2 hours (healthy)
0a4f947f299b        cyberreboot/vent-file-drop:master      "/bin/sh -c '(flask …"   Up 2 hours (healthy)
511f90c6ddd3        cyberreboot/crviz:master               "serve -s build -l 5…"   Up 2 hours (healthy)  
fb250044ff17        cyberreboot/poseidon-api:master        "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
8e898fd68c08        cyberreboot/vent-network-tap:master    "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
552f65d7a982        cyberreboot/vent-rq-worker:master      "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
8dbabe78d1b9        cyberreboot/vent-rq-worker:master      "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
e076452c1515        cyberreboot/vent-rq-worker:master      "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
d0f406f240b1        cyberreboot/vent-rq-worker:master      "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
6229e46723a9        cyberreboot/vent-rq-dashboard:master   "/bin/sh -c '(flask …"   Up 2 hours (healthy)  
5c695040603b        cyberreboot/vent-redis:master          "docker-entrypoint.s…"   Up 2 hours (healthy)  
004e5fdde96e        cyberreboot/vent-syslog:master         "/usr/sbin/syslog-ng…"   Up 2 hours (healthy)  
c0cd7c1f881c        cyberreboot/vent-rabbitmq:master       "docker-entrypoint.s…"   Up 2 hours (healthy)  
d81f5509628c        cyberreboot/vent                       "/bin/sh -c '(flask …"   Up 2 hours (healthy)
```

If you performed the demo installation, you should also see the following Faucet-related containers running (NOTE: Faucet has not yet implemented docker-friendly health checks, so the "(healthy)" reference will not be shown):

```
196f53632485        grafana/grafana:5.2.1                  "/run.sh"                Up 2 hours  
cfb7d68b66e0        prom/prometheus:v2.3.1                 "/bin/prometheus --c…"   Up 2 hours  
86f4188d67f6        faucet/gauge:latest                    "/usr/local/bin/entr…"   Up 2 hours  
2e186573532e        faucet/event-adapter-rabbitmq          "/usr/local/bin/entr…"   Up 2 hours  
c0652a6ccd44        influxdb:1.6-alpine                    "/entrypoint.sh infl…"   Up 2 hours  
2a949b5b1687        faucet/faucet:latest                   "/usr/local/bin/entr…"   Up 2 hours  
```

2. You should see "Poseidon successfully started, capturing logs..." in your syslog output:
```
# journalctl -u poseidon | grep capturing
Jul 25 15:42:20 PoseidonHost poseidon[4273]: Poseidon successfully started, capturing logs...
```

To continue to test (assuming demo installation), please see `/opt/poseidon/docs/demo.txt`, also referenced in the repo above.


## Developing

### Modifying Code that Runs in a Docker Container

If installed as described above, poseidon's codebase will be at `/opt/poseidon`.  At this location, a `.vent_startup.yml` file can be edited to point to a fork of the original repository.  Develop and commit changes on the poseidon fork and use `poseidon -r` to reload and see your changes.
You can verify that it's building against your fork by doing a `docker ps` and the poseidon container will be named off of your fork.

### Modifying Code that Runs on the Host Machine

To make changes to anything outside of the `poseidon` subdirectory you will need to build a new `.deb` and reinstall.
```
git clone <YOUR-POSEIDON-FORK>
cd poseidon
make build_installers
sudo dpkg -i dist/poseidon*.deb
```


## Related Components

- [CRviz](https://github.com/CyberReboot/CRviz)
- [PoseidonML](https://github.com/CyberReboot/poseidonml)
- [Vent](https://github.com/CyberReboot/vent)
- [Vent-Plugins](https://github.com/CyberReboot/vent-plugins)

## Additional Info

- [Authors](AUTHORS)
- Blog posts:
  - [SDN and the need for more (security) verbs](https://blog.cyberreboot.org/sdn-and-the-need-for-more-security-verbs-a6315935fca4)
  - [Introducing Vent](https://blog.cyberreboot.org/introducing-vent-1d883727b624)
  - [Deep Session Learning for Cyber Security](https://blog.cyberreboot.org/deep-session-learning-for-cyber-security-e7c0f6804b81)
  - [Thanks to FAUCET, Poseidon Now Supports Switches Running OpenFlow 1.3](https://blog.cyberreboot.org/thanks-to-faucet-poseidon-now-supports-switches-running-openflow-1-3-e5489f2bc1f5)
  - [Building a Software-Defined Network with Raspberry Pis and a Zodiac FX switch](https://blog.cyberreboot.org/building-a-software-defined-network-with-raspberry-pis-and-a-zodiac-fx-switch-97184032cdc1)
  - [Poseidon with FAUCET SDN Controller](https://blog.cyberreboot.org/poseidon-with-faucet-sdn-controller-b5e78e46660b)
  - [The Case for Detecting Lateral Movement](https://blog.cyberreboot.org/the-case-for-detecting-lateral-movement-2018ae631b04)
  - [TCPDump, and the care and feeding of an intelligent SDN](https://blog.cyberreboot.org/tcpdump-and-the-care-and-feeding-of-an-intelligent-sdn-eca6e7506342)
  - [A better way to visualize what’s on our networks?](https://blog.cyberreboot.org/a-better-way-to-visualize-whats-on-our-networks-4f87fd42da6)
  - [CRviz: Scalable design for network visualization](https://blog.cyberreboot.org/crviz-scalable-design-for-network-visualization-14689133fd91)
  - [CRviz: Initial Release](https://blog.cyberreboot.org/crviz-initial-release-45a3023e0e93)
  - [Using machine learning to classify devices on your network](https://blog.cyberreboot.org/using-machine-learning-to-classify-devices-on-your-network-e9bb98cbfdb6)
- See the latest changes [here](CHANGELOG.md).
- [Code of Conduct](CODE_OF_CONDUCT.md)
- Want to contribute? Awesome! Issue a pull request or see more details [here](CONTRIBUTING.md).
- Developer Guide
- [License](LICENSE)
- [Maintainers](MAINTAINERS)
- [Releases](https://github.com/CyberReboot/poseidon/releases)
- Tests
- [Version](VERSION)
