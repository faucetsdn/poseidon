# Poseidon

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://travis-ci.org/CyberReboot/poseidon.svg?branch=master)](https://travis-ci.org/CyberReboot/poseidon)
[![codecov](https://codecov.io/gh/CyberReboot/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/CyberReboot/poseidon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e31df16fa65447bf8527e366c6271bf3)](https://www.codacy.com/app/CyberReboot/poseidon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CyberReboot/poseidon&amp;utm_campaign=Badge_Grade)
[![Docker Hub Downloads](https://img.shields.io/docker/pulls/cyberreboot/poseidon.svg)](https://hub.docker.com/u/cyberreboot)

> Software Defined Network Situational Awareness

<img src="/docs/img/poseidon-logo.png" width="50" height="75"/><a href="https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/img/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year"></a>

This project is a joint challenge between two IQT Labs: [Cyber Reboot](https://www.cyberreboot.org/) and [Lab41](http://www.lab41.org/). Current software defined network offerings lack tangible security emphasis much less methods to enhance operational security. Without situational awareness and context, defending a network remains a difficult proposition. This project will utilize SDN and machine learning to determine what is on the network, and what is it doing. The goal is to leverage SDN to provide situational awareness and better defend networks.

## Table of Contents

- [Background](#background)
- [Install](#install)
  - [Prerequisites](#prerequisites)
  - [SDN Controller Configuration](#sdn-controller-configuration)
    - [Big Cloud Fabric Configuration](#big-cloud-fabric-configuration)
      - [Span Fabric](#span-fabric)
      - [Interface Group](#interface-group)
    - [Faucet Configuration](#faucet-configuration)
  - [Installing](#installing)
- [Usage](#usage)
- [Examples](#examples)
- [Related Components](#related-components)
- [Additional Info](#additional-info)

## Background

## Install

### Prerequisites

- Bash
- [Docker](https://www.docker.com/) (Poseidon and related components run on top of Docker, so understanding the fundamentals will be useful for troubleshooting as well)
- Make
- An SDN Contrller, specifically [BigSwitch Cloud Fabric](https://www.bigswitch.com/products/big-cloud-fabric) or [Faucet](https://faucet.nz/)
- Debian Linux (if installing with the `DEB` which is the recommended install choice)
  - Currently supported versions are:
    - Ubuntu 14.04
    - Ubuntu 16.04
    - Ubuntu 17.10
    - Ubuntu 18.04
    - Uubntu 18.10

### SDN Controller Configurtion
Before getting started, one of the two supported controllers (*BigSwitch Cloud Fabric* or *Faucet*) needs to running and accessible to where Poseidon will be deployed.

#### Big Cloud Fabric Configuration
<img src="/docs/img/bcf.png" width="114" height="100"/>
You will need to add support for moving arbitrary endpoint data around your network.  The BigSwitch config will need an admin who will need to add:

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

Poseidon will connect to BCF using its REST API, so you'll need the API endpoint and credentials to it.

BCF is now configured and ready for use with Poseidon.

#### Faucet Configuration
<img src="/docs/img/faucet.png" width="190" height="100">
Poseidon requires at least Faucet version 1.8.6 or higher.

Unless Poseidon and Faucet are running on the same host, Poseidon will connect to Faucet using SSH.  So you'll need to create an account that can SSH to the machine running Faucet and that has rights to modify the configuration file `faucet.yaml` (currently Poseidon expects it to be in the default `/etc/faucet/faucet.yaml` location and `dps` must all be defined in this file for Poseidon to update the network posture correctly).

Faucet needs to be started with the following environment variables set:
```
export FAUCET_EVENT_SOCK=1
export FAUCET_CONFIG_STAT_RELOAD=1
```

If using the [RabbitMQ adapter for Faucet](https://github.com/faucetsdn/faucet/tree/master/adapters/vendors/rabbitmq) (recommended) make sure to also export `FA_RABBIT_HOST` to the IP address of where Poseidon will be running.

Faucet is now configured and ready for use with Poseidon.


### Installing

```
sudo apt-get install -y apt-transport-https
curl -sLf "https://dl.cloudsmith.io/public/cyberreboot/poseidon/cfg/gpg/gpg.F9E23875C98A1F72.key" | sudo apt-key add -
sudo curl -o /etc/apt/sources.list.d/cyberreboot-poseidon.list -sLf "https://dl.cloudsmith.io/public/cyberreboot/poseidon/cfg/install/config.deb.txt?os=ubuntu&version=$(lsb_release -rs)&dist=$(lsb_release -cs)"
sudo apt-get update
sudo apt-get install poseidon
```

## Usage

After installation you'll have a new command `poseidon` available for looking at the status, logs, changing the configuration or stopping and starting the service.
```
poseidon help
```

Results of Poseidon are printed out in the logs.

## Examples

TODO

## Related Components

- [CRviz](https://github.com/CyberReboot/CRviz)
- [PoseidonML](https://github.com/CyberReboot/poseidonml)
- [Vent](https://github.com/CyberReboot/vent)
- [Vent-Plugins](https://github.com/CyberReboot/vent-plugins)

## Additional Info

- [Authors](AUTHORS)
- See the latest changes [here](CHANGELOG.md).
- [Code of Conduct](CODE_OF_CONDUCT.md)
- Want to contribute? Awesome! Issue a pull request or see more details [here](CONTRIBUTING.md).
- Developer Guide
- [License](LICENSE)
- [Maintainers](MAINTAINERS)
- Tests
- [Version](VERSION)
