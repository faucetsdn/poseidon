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
  - [Installing](#installing)
- [Usage](#usage)
- [Examples](#examples)
- [Related Components](#related-components)
- [Additional Info](#additional-info)

## Background

## Install

### Prerequisites

- Bash
- [Docker](https://www.docker.com/)
- Make
- Debian Linux (if installing with the `DEB` which is the recommended install choice)
  - Currently supported versions are:
    - Ubuntu 14.04
    - Ubuntu 16.04
    - Ubuntu 17.10
    - Ubuntu 18.04
    - Uubntu 18.10

### Installing

```
sudo apt-get install -y apt-transport-https
curl -sLf "https://dl.cloudsmith.io/public/cyberreboot/poseidon/cfg/gpg/gpg.F9E23875C98A1F72.key" | sudo apt-key add -
sudo curl -o /etc/apt/sources.list.d/cyberreboot-poseidon.list -sLf "https://dl.cloudsmith.io/public/cyberreboot/poseidon/cfg/install/config.deb.txt?os=ubuntu&version=$(lsb_release -rs)&dist=$(lsb_release -cs)"
sudo apt-get update
sudo apt-get install poseidon
```

## Usage

## Examples

## Related Components

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


### Quick Start
Poseidon currently supports two different SDN controllers, [Big Cloud Fabric](https://www.bigswitch.com/products/big-cloud-fabrictm/switching-fabric-overview) and [FAUCET](https://github.com/faucetsdn/faucet).

<img src="/docs/img/bcf.png" width="114" height="100"/><img src="/docs/img/faucet.png" width="190" height="100">

Before getting started, one of these two controllers needs to running and accessible to where Poseidon will be deployed.  Skip to the controller section that you wish to deploy.

#### Big Cloud Fabric (BCF) Configuration
You will need to add support for moving arbitrary endpoint data around your network.  The BigSwitch config will need an admin who will need to add:

- span-fabric
- interface-group

##### span-fabric

Replace `<name>` with the name of your span-fabric and `<interface-group>` with the name of your interface-group.
```
! span-fabric
span-fabric <name>
  active
  destination interface-group <interface-group>
  priority 1
```

##### interface-group

Replace `<interface-group>` with the name of your interface-group. Additionally fill in the `YOUR_LEAF_SWITCH` and `YOUR_INTERFACE_WHERE_VENT_WILL_RECORD_TRAFFIC_FROM`.
```
! interface-group
interface-group <interface-group>
  description 'packets get mirrored here to be processed'
  mode span-fabric
  member switch YOUR_LEAF_SWITCH interface YOUR_INTERFACE_WHERE_VENT_WILL_RECORD_TRAFFIC_FROM
```

Poseidon will connect to BCF using its REST API, so you'll need the API endpoint and credentials to it.  The easiest way to set these values so that Poseidon can use them is in environment variables like so (assuming the controller is running at `192.168.1.10`):

```
export controller_type=bcf
export controller_uri=https://192.168.1.10:8443/api/v1/
export controller_user=user
export controller_pass=pass
export controller_span_fabric_name=name
export controller_interface_group=interface-group
```

BCF is now configured and ready for use with Poseidon, continue on to the [Starting Poseidon using Vent](#starting-poseidon-using-vent) section.

#### FAUCET Configuration
Poseidon requires at least FAUCET version 1.8.6 or higher.

Unless Poseidon and FAUCET are running on the same host, Poseidon will connect to FAUCET using SSH.  So you'll need to create an account that can SSH to the machine running FAUCET and that has rights to modify the configuration file `faucet.yaml` (currently Poseidon expects it to be in the default `/etc/faucet/faucet.yaml` location and `dps` must all be defined in this file for Poseidon to update the network posture correctly).  The easiest way to set these values so that Poseidon can use them is in environment variables like so (assuming the controller is running at `192.168.1.10`):

```
export controller_type=faucet
export controller_uri=192.168.1.10
export controller_user=user
export controller_pass=pass
export controller_log_file=/var/log/faucet/faucet.log
export controller_config_file=/etc/faucet/faucet.yaml
export controller_mirror_ports='{"switch1":3}'  # a python dictionary of switch names (from faucet.yaml) and switch port numbers for mirroring to
```

If Poseidon and FAUCET are running on the same host, `controller_user` and `controller_pass` do not need to be set. `controller_uri` should be exported like so:
```
export controller_uri=
```

FAUCET is now configured and ready for use with Poseidon, continue on to the [Starting Poseidon using Vent](#starting-poseidon-using-vent) section.

#### Starting Poseidon using Vent
[Vent](https://github.com/CyberReboot/vent) is a platform we built to automate network collection and analysis pipelines, such as the ones that Poseidon would need.  Leveraging Vent, we can specify all of the actions we expect Poseidon to be able to do from network event (i.e. new device plugged in), to network capture, to analysis, and closing the loop by feeding back an actionable decision.

In order to run Poseidon in Vent, regardless of the SDN controller chosen, a few additional environment variables need to be set:

```
export collector_nic=eth0  # set the NIC of the machine that traffic will be mirrored to
export max_concurrent_reinvestigations=1  # number of active simultaneous mirror operations you want to support
```

Start Vent with:

```
./helpers/run
```

Once Vent is finished starting things up, you'll be able to see the logs of everything, including Poseidon by running:

```
docker logs -f cyberreboot-vent-syslog-master
```

If you quit out of the vent container, you can start it again with:

```
docker start vent
```

And then attach to the console with:

```
docker attach vent
```

* Note: if use Docker for Mac, you'll need to create a directory `/opt/vent_files` and add it to shared directories in preferences.

## Installing
If you prefer to orchestrate all of the pieces for Poseidon yourself without Vent, then follow these directions:

```
git clone https://github.com/CyberReboot/poseidon.git
cd poseidon
*editor* config/poseidon.config
docker build -t poseidon .
docker run poseidon
```

### Configuration

**config/poseidon.config**

```
[Monitor]

rabbit_server =  RABBIT_SERVER  # ip address of the rabbit-mq server
rabbit_port = RABBIT_PORT  # rabbit-mq server server port
collector_nic = COLLECTOR_NIC  # name of the network interface that will be listening for packets 
vent_ip = vent_ip  # ip address of server running vent 
vent_port = VENT_PORT  # vent server port

[NorthBoundControllerAbstraction:Update_Switch_State]
controller_uri = https://CONTROLLER_SERVER:8443/api/v1/  # example for BCF controller ip 
controller_user = USERNAME  # username for BCF login
controller_pass = PASSWORD  # password for BCF login
controller_type = CONTROLLER  # either `bcf` or `faucet`
```

## Makefile Options

You can use `make` to simplify the building process.  This is primarily useful for development.
To build the container, simply run:

```
git clone https://github.com/CyberReboot/poseidon.git
cd poseidon
make build_poseidon
```

To build and run the container, run this command from inside the poseidon directory:

```
make run_poseidon
```

This first builds poseidon, then runs it. After it finishes running, the container is removed.

To populate the current volume with the contents of the containers' "poseidonWork/" directory, run:

```
make run_dev
```

To run poseidon with sh as entrypoint, run:

```
make run_sh
```

This also removes the container after it has finished running.

If you want to build the docs, then invoke:

```
make build_docs
```

To build and then open the docs in a container on port 8080:

```
make run_docs
```

To run tests:

```
make run_tests
```

## Running the tests
Tests are currently written in py.test for Python.  The tests are automatically run when opening Pull Requests to Poseidon.

## Contributing
Want to contribute?  Awesome!  Issue a pull request or see more details [here](https://github.com/CyberReboot/poseidon/blob/master/CONTRIBUTING.md).

## Authors

* [Poseidon Team](https://github.com/CyberReboot/poseidon/blob/master/AUTHORS)

See also the list of [contributors](https://github.com/CyberReboot/poseidon/graphs/contributors) who participated in this project.

## License

This project is licensed under the Apache License - see the [LICENSE.md](LICENSE.md) file for details

## Documentation
- [Additional Documentation](https://github.com/CyberReboot/poseidon/tree/master/docs)












