#  We are coding again. After a brief pause we are ready to extend Poseidon. Look for additional refinements to the machine learning, a simpler architecture, and better results. 

# Status
Currently the code is going through a simplification stage.  Many classes are being axed to get things to run in a single docker container.  The code at this point is not functional.

# Poseidon
![Poseidon Logo](/docs/fork.png) <a href="https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year"></a>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CircleCI](https://circleci.com/gh/CyberReboot/poseidon.svg?style=shield)](https://circleci.com/gh/CyberReboot/poseidon)
[![codecov](https://codecov.io/gh/Lab41/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/Lab41/poseidon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3ea08f0c632148538f6f947677f42aa2)](https://www.codacy.com/app/d-grossman/poseidon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Lab41/poseidon&amp;utm_campaign=Badge_Grade)

Situational awareness underpins informed decisions. Understanding what comprises a network, and what network elements are doing is essential.  Without situational awareness and context, defending a network remains a difficult proposition.

Can SDN and machine learning answer:
- What devices comprise my network?
- What are devices doing?

# Install Instructions
```
git clone https://github.com/CyberReboot/poseidon.git
cd poseidon
*editor* config/poseidon.config
docker build -f ./Dockerfile -t poseidon .
docker run poseidon
```

# Configuration

## config/poseidon.config
### Monitor
- Under the `[Monitor]` section, update the following:
- `rabbit-server` to the external ip of the vent rabbit server
- `rabbit-port` to the port that the vent rabbit server is running

### NorthBoundControllerAbstraction:Update_Switch_State
- Under `[NorthBoundControllerAbstraction:Update_Switch_State]` section, update the following:
- `controller_uri` to the url for your controller
- `controller_user` username for logging into your controller
- `controller_pass` password for logging into your controller

### the following will be removed/moving around..
- `collection` to the name of the collection storing the network graph documents (default is `netgraph_beta`)
- `collector_nic` to the nic on the machine running vent that is configured with the controller to capture traffic
- `collector_interval` to the collection interval in seconds (default is `30` for a capture length of 30 seconds)
- `collector_filter` to limit what gets captured off the controller (default is empty string for no filters, see the collector documentation for details)
- `vent_ip` to the ip of the box running the vent collector
- `vent_port` to the external port of the nfilter vent container 
- `storage_interface_ip` to the external ip of the poseidon-storage-interface container (NOTE: this should be the same as the `database` field of `PoseidonStorage`, unlesss the storage-interface container is being run on a different machine)
- `storage_interface_port` to the external port of the poseidon-storage-interface container only if changed from the default of `28000`

# Required Dependencies
- Docker

# Documentation
- [Docs](https://github.com/Lab41/poseidon/tree/master/docs)

# Tests
Tests are currently written in py.test for Python.  The tests are automatically run when building the containers.

# Contributing to Poseidon
Want to contribute?  Awesome!  Issue a pull request or see more details [here](https://github.com/Lab41/poseidon/blob/master/CONTRIBUTING.md).
