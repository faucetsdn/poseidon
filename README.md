# Poseidon
<img src="/docs/img/poseidon-logo.png" width="50" height="75"/><a href="https://www.blackducksoftware.com/open-source-rookies-2016" ><img src="/docs/img/Rookies16Badge_1.png" width="100" alt="POSEIDON is now BlackDuck 2016 OpenSource Rookie of the year"></a>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CircleCI](https://circleci.com/gh/CyberReboot/poseidon.svg?style=shield)](https://circleci.com/gh/CyberReboot/poseidon)
[![codecov](https://codecov.io/gh/CyberReboot/poseidon/branch/master/graph/badge.svg?token=ORXmFYC3MM)](https://codecov.io/gh/CyberReboot/poseidon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3ea08f0c632148538f6f947677f42aa2)](https://www.codacy.com/app/d-grossman/poseidon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CyberReboot/poseidon&amp;utm_campaign=Badge_Grade)

Software Defined Network Situational Awareness

This challenge is a joint challenge between two IQT Labs: Lab41 and Cyber Reboot. Current software defined network offerings lack tangible security emphasis much less methods to enhance operational security. Without situational awareness and context, defending a network remains a difficult proposition. This challenge will utilize SDN and machine learning to determine what is on the network, and what is it doing. This goal will help sponsors leverage SDN to provide situational awareness and better defend their networks.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites
[Docker Installed](https://www.docker.com/)

### Installing
```
git clone https://github.com/CyberReboot/poseidon.git
cd poseidon
*editor* config/poseidon.config
docker build -f ./Dockerfile.poseidon -t poseidon .
docker run poseidon
```

### Makefile Options

You can use `make` to simplify the building process.
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

## Configuration
config/poseidon.config
### [Monitor]
rabbit_server =  `RABBIT_SERVER`  
rabbit_port = `RABBIT_PORT`  
collector_nic = `COLLECTOR_NIC`  
vent_ip = `vent_ip`  
vent_port = `VENT_PORT`  
  
`RABBIT_SERVER` - ip address of the rabbit-mq server   
`RABBIT_PORT` - rabbit-mq server server port  
`COLLECTOR_NIC` - name of the network interface that will be listening for packets  
`vent_ip` - ip address of serever running vent  
`VENT_PORT` - vent server port  

### [NorthBoundControllerAbstraction:Update_Switch_State]
controller_uri = https://`CONTROLLER_SERVER`:8443/api/v1/  
controller_user = `USERNAME`  
controller_pass = `PASSWORD`  
controller_type = `CONTROLLER`

`CONTROLLER_SERVER` - BCF controller ip  
`USERNAME` - username for BCF login  
`PASSWORD` - password for BCF login
`CONTROLLER` - either `bcf` or `faucet`



## Running Poseidon with Vent

Export `controller_uri`, `controller_user`, and `controller_pass` environment variables to match your connection details for your BCF controller.
Also make any additional configuration changes to `.plugin_config.yml`

```
export controller_uri=https://x.x.x.x:8443/api/v1/
export controller_user=user
export controller_pass=pass
```

```
git clone https://github.com/CyberReboot/poseidon.git
cd poseidon
docker run -it \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /opt/vent_files:/opt/vent_files \
           -v $(pwd)/.plugin_config.yml:/root/.plugin_config.yml \
           -v $(pwd)/.vent_startup.yml:/root/.vent_startup.yml \
           -e controller_uri=$controller_uri \
           -e controller_user=$controller_user \
           -e controller_pass=$controller_pass \
           -e controller_type=$controller_type \
           --name vent \
           cyberreboot/vent
```

* Note: if use Docker for Mac, you'll need to create a directory `/opt/vent_files` and add it to shared directories in preferences.

## Bigswitch configuration modifications
you will need to add support for moving arbitrary endpoint data around your network.  The bigswitch config will need an admin will need to add
1. span-fabric
1. interface-group

### span-fabric


```
! span-fabric
span-fabric vent
  active
  destination interface-group ig1
  priority 1
```

### interface-group
```
! interface-group
interface-group ig1
  description 'packets get mirrored here to be processed'
  mode span-fabric
  member switch YOUR_LEAF_SWITCH interface YOUR_INTERFACE_WHERE_VENT_WILL_RECORD_TRAFFIC_FROM
```

### NOTE:

If the interface-group `ig1` is reserved in your install, you will need to modify dest-interface-group in:
```
poseidon/poseidonMonitor/NorthBoundControllerAbstraction/proxy/bcf/bcf.py:            "dest-interface-group": "ig1",
poseidon/poseidonMonitor/NorthBoundControllerAbstraction/proxy/bcf/sample_state.py:    "dest-interface-group": "ig1",
```

if the span-fabrc `vent` is reserved in your install, you will need to modify the span_name, and other variables in:
```
/poseidon/poseidonMonitor/NorthBoundControllerAbstraction/proxy/bcf/bcf.py
/poseidon/poseidonMonitor/NorthBoundControllerAbstraction/proxy/bcf/test_bcf.py
/poseidon/poseidonMonitor/NorthBoundControllerAbstraction/proxy/bcf/sample_state.py
```

To look at the logs:

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

## Running the tests
Tests are currently written in py.test for Python.  The tests are automatically run when building the containers.

## Contributing
Want to contribute?  Awesome!  Issue a pull request or see more details [here](https://github.com/CyberReboot/poseidon/blob/master/CONTRIBUTING.md).

## Authors

* [Lab41 Poseidon Team](https://github.com/CyberReboot/poseidon)

See also the list of [contributors](https://github.com/CyberReboot/poseidon/graphs/contributors) who participated in this project.

## License

This project is licensed under the Apache License - see the [LICENSE.md](LICENSE.md) file for details

## Documentation
- [Additional Documentation](https://github.com/CyberReboot/poseidon/tree/master/docs)












