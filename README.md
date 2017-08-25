#  We are coding again. After a brief pause we are ready to extend Poseidon. Look for additional refinements to the machine learning, a simpler architecture, and better results. 

# Poseidon
![Poseidon Logo](/docs/fork.png) <a href="https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year"></a>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://circleci.com/gh/Lab41/poseidon.svg?style=shield&circle-token=29305a2d23d6cac65f811620d75bbe80732472dd)](https://circleci.com/gh/Lab41/poseidon) [![codecov](https://codecov.io/gh/Lab41/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/Lab41/poseidon)

Situational awareness underpins informed decisions. Understanding what comprises a network, and what network elements are doing is essential.  Without situational awareness and context, defending a network remains a difficult proposition.

Can SDN and machine learning answer:
- What devices comprise my network?
- What are devices doing?

# Install Instructions
```
sudo mkdir -p /data/db
git clone https://github.com/Lab41/poseidon.git
cd poseidon
*editor* config/poseidon.config
make compose
```

# Configuration
## docker-compose.yaml
- `/data/db` directory for mongodb database; you can use a different directory by updating the `docker-compose.yaml` 
- under the `storage` section, update `volumes` to `/path/to/your/dir:/data/db` with the path to the directory to store mongodb records.

## config/poseidon.config
### PoseidonStorage
- Under the `[PoseidonStorage]` section, update the following:
- `database` to the external ip of the host machine running mongodb (or
the `docker-machine ip` if using boot2docker or similar - making sure that write-persistent volumes can be mounted). NOTE: without this configuration, poseidon will fail to build.

### PoseidonMain
- Under `[PoseidonMain]` section, update the following:
- `database` to the name of the database storing the network graph documents (default is `poseidon_records`)
- `collection` to the name of the collection storing the network graph documents (default is `netgraph_beta`)
- `collector_nic` to the nic on the machine running vent that is configured with the controller to capture traffic
- `collector_interval` to the collection interval in seconds (default is `30` for a capture length of 30 seconds)
- `collector_filter` to limit what gets captured off the controller (default is empty string for no filters, see the collector documentation for details)
- `vent_ip` to the ip of the box running the vent collector
- `vent_port` to the external port of the nfilter vent container 
- `storage_interface_ip` to the external ip of the poseidon-storage-interface container (NOTE: this should be the same as the `database` field of `PoseidonStorage`, unlesss the storage-interface container is being run on a different machine)
- `storage_interface_port` to the external port of the poseidon-storage-interface container only if changed from the default of `28000`

### Controller
- Update the `controller_uri` ip address, `contrller_user`, `controller_pass` of the `[NorthBoundControllerAbstraction:Handle_Periodic]` section. NOTE: without this configuration, poseidon will not be able to talk to the controller

# Required Dependencies
- Docker (If installing from a clean machine, a startup.sh script resides in the repo that can be used to 
install docker and docker-compose for an Ubunut 16.04 box. Make this script executable and then 
run with `sudo ./startup.sh`.)
- make
- docker-compose (the 1.8 release of docker-compose can be installed with `make compose-install`)

# Documentation
- [Docs](https://github.com/Lab41/poseidon/tree/master/docs)

# Tests
Tests are currently written in py.test for Python.  The tests are automatically run when building the containers.

They can also be tested using:
```
make test
```

# build is broke and is talking about docker-compose not working
Installing docker-compose is usually a seperate event to installing docker.  Even if you installed docker-compose it may not be the most recent version.  The version that works with our `docker-compose.yaml`:

docker-compose version

```
docker-compose version 1.8.0, build f3628c7
docker-py version: 1.9.0
CPython version: 2.7.9
OpenSSL version: OpenSSL 1.0.1e 11 Feb 2013
```

the latest version of compose can always be pulled from the [docker repo](https://github.com/docker/compose/releases)
# Contributing to Poseidon
Want to contribute?  Awesome!  Issue a pull request or see more details [here](https://github.com/Lab41/poseidon/blob/master/CONTRIBUTING.md).
