# Poseidon
![Poseidon Logo](/docs/fork.png)

[![Build Status](https://circleci.com/gh/Lab41/poseidon.svg?style=shield&circle-token=29305a2d23d6cac65f811620d75bbe80732472dd)](https://circleci.com/gh/Lab41/poseidon) [![codecov](https://codecov.io/gh/Lab41/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/Lab41/poseidon)

Situational awareness underpins informed decisions. Understanding what comprises a network, and what network elements are doing is essential.  Without situational awareness and context, defending a network remains a difficult proposition.

Can SDN and machine learning answer:
- What devices comprise my network?
- What are devices doing?

# Getting Started

# Install Instructions

```
sudo mkdir -p /data/db
git clone https://github.com/Lab41/poseidon.git
cd poseidon
make
```

If installing from a clean machine, a startup.sh script resides in the repo that can be used to 
install docker and docker-compose for an Ubunut 16.04 box. Make this script executable and then 
run with `sudo ./startup.sh`.

# Required Dependencies

- Docker
- make
- docker-compose
- `/data/db` directory for mongodb database; you can use a different directory by updating the `docker-compose.yaml` 
- under the `storage` section, update `volumes` to `/path/to/your/dir:/data/db` with the path to the directory to store mongodb records.
- The 1.8 release of docker-compose can be installed with `make compose-install`
- Update the `ip` of the `[database]` section of `config/poseidon.config` to the external ip of the host machine running mongodb (or
the `docker-machine ip` if using boot2docker or similar). NOTE: without this configuration, poseidon will fail to build.
- Update the `controller_uri` ip address, `contrller_user`, `controller_password` of the `[NorthBoundControllerAbstraction:Handle_Periodic]` NOTE: without this configuration, poseidon will not be able to talk to the controller

# Usage Examples

```
make compose
```

# Documentation
- [Docs](https://github.com/Lab41/poseidon/tree/master/docs)

# Tests

Tests are currently written in py.test for Python.  The tests are automatically run when building the dockerfile.

They can also be tested using:
```
make test
```

# Contributing to Poseidon

Want to contribute?  Awesome!  Issue a pull request or see more details [here](https://github.com/Lab41/poseidon/blob/master/CONTRIBUTING.md).
