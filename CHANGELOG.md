# v0.17.3 (2020-01-15)

* Fix networkml no results.

# v0.17.2 (2020-01-14)

* Major restructuring of codebase, maintaining same functionality
* Updated poseidon script to use git clone instead of tar file from releases for pbr
* Added certstrap to the same poseidon network for docker-compose, so there is only one network instead of two
* Updated docker, transitions, codecov, prometheus, faucetconfrpc, network_tap, certstrap, greenlet, and grafana

# v0.17.1 (2020-12-22)

* Reduce overhead of processing unneed Faucet events.
* Fix arm releases
* Upgrade codecov

# v0.17.0 (2020-12-21)

* Move to PBR/package for posiedon core, api, cli
* Add generic receive of pcap tool parsing support.
* Upgrade grafana, pytype

# v0.16.0 (2020-12-17)

* Remove Redis storage, move to Prometheus
* Remove active/inactive endpoint states (endpoints now will expire over time if not observed)
* Updated NetworkML, faucet, gauge, event-adapter-rabbitmq, faucetconfrpc, certstrap, prometheus, grafana, requests, pytype, mock, pytest

# v0.15.9 (2020-11-25)

* Refactored RabbitMQ connections, processing Faucet events, and cleanly exiting.
* Removed behavior from states and NetworkML results as it no longer being used in NetworkML
* Updated NetworkML, pre-commit, event-adapter-rabbitmq, certstrap, faucetconfrpc, pytype, grafana, and docker
* Cleaned up formatting and style

# v0.15.8 (2020-11-20)

* Incremental refactoring to simplify tests and main.py
* Move to faucetconfrpc add/remove/clear port mirror RPCs
* Updated faucetconfrpc, certstrap, faucet, gauge, grafana, codecov, prometheus, pytype, urllib3, cmd2, requests, networkml, transitions

# v0.15.7 (2020-10-30)

* Upgrade networkml, faucetconfrpc, faucet, gauge, httmock, grafana, pytest, event-adapter-rabbitmq, certstrap

# v0.15.6 (2020-10-23)

* Speed up DNS resolution (parallel)
* Poseidon can use its own grpc client key
* Upgrade network-tools, networkml, pytype, transitions, prometheus, urllib3, faucet, faucetconfrpc, grafana

# v0.15.5 (2020-10-09)

* Add e2e test, reduce size of poseidon and poseidon-api containers.
* Updated faucetconfrpc, certstrap, pytype, transistions, pytest, cmd2, faucet, gauge, grafana

# v0.15.4 (2020-09-18)

* Updated faucetconfrpc (move certstrap to faucetconfrpc)
* Fix handling of empty faucet.yaml
* Updated pytype, pytest, prometheus, texttable, ruamel.yaml, cmd2

# v0.15.3 (2020-09-04)

* Updated cmd2, pytype, faucetconfrpc

# v0.15.2 (2020-08-27)

* Updated faucet, gauge, grafana, rabbitmq, faucetconfrpc, cmd2, docker, pylint, pytest-cov, and pytype
* Clean up RPC calls to Faucet

# v0.15.1 (2020-08-14)

* Fix certstrap created certificates (old faucetconfrpc certificates must be removed, will be automatically recreated)
* Use more specific faucetconfrpc write RPCs to fix conflicts with other RPC applications.
* updated network-tools, cmd2, docker, faucetconfrpc, pytype, urllib3, grafana

# v0.15.0 (2020-08-06)

* updated faucetconfrpc (and certificates move to /opt/faucetconfrpc by default).
* updated to networkml 0.6.0
* repo move from cyberreboot to iqtlabs
* updated cmd2, faucet, grafana, prometheus, pytype

# v0.14.3 (2020-07-31)

* Internal refactoring for faucetconfrpc compatibility
* updated faucetconfrpc, networkml, pytest, docker, urllib3, pytype, crviz

# v0.14.2 (2020-07-17)

* updated faucetconfrpc, crviz

# v0.14.1 (2020-07-17)

* Internal refactoring to simplify ACL processing.
* Updated network-tap, pytype, cmd2, faucet, gauge, faucetconfrpc, grafana, netaddr.

# v0.14.0 (2020-07-02)

- Poseidon now uses faucetconfrpc to manage Faucet's config files (controller_config_file is obsolete)
- controller_uri, rabbit_enabled, rabbit_server, rabbit_port all obsolete (Poseidon will always use its own rabbit server)
- Poseidon no longer supports Faucet log parsing to retrieve events (default remains the Faucet event API)
- Poseidon can now mirror leaf switches like (WiFi APs) by mirroring the port on a neighboring switch (see controller_proxy_mirror_ports)
- Changed from alpine:3.12 to debian/python:3.8-slim to reduce build times.
- Updated docker, netaddr, transitions, pytype, faucet, gauge, faucet-adapter-rabbitmq, grafana, prometheus, networkml, network-tools

# v0.13.0 (2020-06-18)

- Removed support for BCF (BigSwitch Cloud Fabric)
- Better cleanup of services when using docker swarm
- Faucet tunnels are now used for mirroring, allowing multi-switch mirroring to a single location
- Updated faucet, gauge, event-adapter-rabbitmq, cmd2, requests, pylint, pytest-cov, buildx

# v0.12.3 (2020-06-05)

- BCF (Bigswitch Cloud Fabric) support is deprecated and will be removed in the next release
- Experimental support for docker swarms
- When FAUCET stacking is detected, do not redundantly learn endpoints on stack links
- Update faucet, gauge, event-adapter-rabbit-mq, buildx, pytype, docker, redis, grafana, pytest


# v0.12.2 (2020-05-21)

- Fix API not updated with networkml/p0f results.
- Update pytest, redis, faucet, gauge, pytype, grafana.


# v0.12.1 (2020-05-08)

- networkml 0.5.4 (can return multiple results)
- Poseidon can parse multiple results from both networkml and p0f
- Poseidon does atomic replace of FAUCET config files
- Update faucet, gauge, event-adapter-rabbit-mq, pylint, prometheus


# v0.12.0 (2020-04-30)

- Major update networkml to 0.5.3 (complete implementation change from v0.4.x)
- p0f and networkml no longer update redis, now done by poseidon
- Update faucet, gauge, event-adapter-rabbit-mq, pytype, network-tap, pylint, codecov, grafana, prometheus


# v0.11.2 (2020-04-10)

- Update faucet, gauge, event-adapter-rabbit-mq, network-tap, pytype, cmd2, flask, transitions


# v0.11.1 (2020-03-26)

- crviz to v0.3.21
- Update faucet, gauge, event-adapter-rabbit-mq, pytest, prometheus, transitions, grafana, pyyaml, cmd2, mock
- refactor for future FAUCET tunneling support


# v0.11.0 (2020-02-28)

- Update faucet, gauge, event-adapter-rabbit-mq
- Add config infrastructure for Volos (should copy new VOLOS and PIPETTE sections into existing poseidon.config)


# v0.10.3 (2020-02-21)

- network-tools v0.11.4, networkml v0.4.8 (fix no results from networkml).
- Add KEEPIMAGES diagnostic environment variable to keep containers.
- Update grafana, requests, cmd2, faucet, gauge, event-adapter-rabbit-mq
- Initial Volos infrastructure.


# v0.10.2 (2020-02-13)

- Fix stale images for ncapture and rabbitmq.


# v0.10.1 (2020-02-13)

- Linux arm7 and arm64 now supported via Docker.
- NetworkML now run against combined pcap (one to many) rather than host to host.
- Add new gen_pcap_manifest.py script to aid curation of pcaps by MAC or IP.
- Move to github actions rather than TravisCI.
- Upgraded versions of NetworkML, CRViz and network-tools
- New versions of mock, pytype, redis, pytest, grafana, urllib3, cmd2


# v0.10.0 (2020-01-16)

- Poseidon is now completely docker-compose only; remove all vestiges of vent. Pcap logs are now logged in /opt/poseidon_files not /opt/vent_files
- New versions of pyyaml, pytype, cmd2, transitions, grafana, CRviz, network-tap, NetworkML, pcap-to-node-pcap, tcprewrite-dot1q, p0f


# v0.9.0 (2020-01-02)

- Updated version of prometheus
- Moved orchestrator from Vent to docker-compose
- Removed .deb package now that it can be run with docker-compose

# v0.8.1 (2019-12-19)

- Updated versions of grafana, pytest, pytype, cmd2
- Updated versions of NetworkML, CRviz, and vent-plugins

# v0.8.0 (2019-12-05)

- Updated versions of grafana, pytest, cmd2, gunicorn, pytype, pyyaml

# v0.7.9 (2019-11-22)

- Updated versions of urllib3, prometheus, cmd2, pylint, and pytest
- Added more documentation
- Added extra protocol label field to CLI
- Fixed missing event data for ACL history
- Added more tests

# v0.7.8 (2019-11-08)

- Fix bug where jq wasn't already on the system installing the deb

# v0.7.7 (2019-11-08)

- Updated versions grafana/grafana Docker tag
- Added property audit logging for behavior and OS
- Fixed pytype checks
- Added mirror port checks

# v0.7.6 (2019-10-25)

- Updated versions of redis, pytest, cmd2, grafana, prometheus, pylint, and pytype
- Added volume for Faucet UDS
- Added more files to ignore in Docker container
- Added API endpoint to retrieve data by IP
- Added ability to apply ACLs with RabbitMQ message
- Ensure VLAN is a string
- Persist Vent info in a volume

# v0.7.5 (2019-10-11)

- Updated versions of prometheus, pytest-cov, pytest, grafana, and redis
- Fixed some typos in the documentation
- Added a warning about max time between investigations
- Added ACLs to the CLI and the API
- Using ipaddress library for ip addresses now
- Added pytype checks
- Fixed filtering for ipv4/ipv6 in the CLI

# v0.7.4 (2019-10-03)

- Fix key checks for automated ACLs

# v0.7.3 (2019-10-03)

- Updated versions of urllib3, pytest, grafana, cmd2, and pylint
- Now uses the auto revert feature of Faucet when using the helper run script
- Endpoints are now a dictionary instead of a list to prevent duplicates
- Fixed an issue where messages from ncapture weren't being handled correctly
- Fixed an issue where the investigations count could be wrong
- Resets the debconf response for collector_nics when not in use
- Debconf option for setting the reinvestigation frequency
- Fixed viz command for Poseidon script
- Handle IP addresses being None
- Better diff of when endpoints change

# v0.7.2 (2019-09-17)

 - Added type entries to history
 - Fixed an issue where queue was being triggered on inactive endpoints
 - Fixed the IP for the `run` helper Faucet script
 - Fixed some instances of the wrong member being called in main
 - Force triggering a transition when ncaptures complete

# v0.7.1 (2019-09-13)

 - Updated versions of pytest and transitions
 - Fixed error where VLAN wasn't getting properly stored
 - Updated demo.txt to match current output
 - CLI can now output in CSV, JSON, and table formats
 - Updated CRviz integration URL
 - Slightly improved state transitions
 - Fix several bugs in the automated ACLs

# v0.7.0 (2019-08-30)

 - Added experimental support for automated ACL changes with Faucet
 - Added two new fields for the config: automated_acls and rules_file

# v0.6.7 (2019-08-21)

 - Updated versions of redis, transitions, and pytest
 - Packaged new version of vent v0.9.8

# v0.6.6 (2019-08-02)

 - Updated versions of cmd2, redis, pip, and pytest
 - updated for new NetworkML message format
 - Removed Support for Ubuntu 18.10 (Cosmic Cuttlefish)

# v0.6.5 (2019-08-02)

 - Updated versions of cmd2, pika, redis, and pyyaml
 - introduced release scripts

# v0.6.4 (2019-07-12)

 - Updated versions of cmd2, pytest, flask, and texttable

# v0.6.3 (2019-06-28)

 - Updated versions of cmd2, ubuntu, alpine, prometheus_client
 - Added sudo for creating log file in the helper script

# v0.6.2 (2019-06-14)

 - Updated versions of pytest, prometheus_client, pyyaml
 - Packaged new version of components, including vent v0.9.3, CRviz v0.3.4, and  NetworkML v0.3.3
 - Fixed VLAN issue for BCF
 - Renamed tenant to VLAN
 - Fixed the namespace label for using a fork of Poseidon
 - Fixed bug where config differences broke git

# v0.6.1 (2019-05-31)

 - Packaged new version of components, including vent v0.9.2, CRviz v0.3.3, and PoseidonML v0.3.2
 - Updated versions of urllib3, requests, and flask
 - Fixed a bug where subnet could get set to './24'

# v0.6.0 (2019-05-13)

 - Packaged new version of components, including vent v0.9.1
 - Fixed header in certain cases for IPv4 and IPv6 in the CLI
 - Updated versions of mock and pytest
 - Support for multiple collector nics across multiple switches for Faucet
 - Support for ignoring specific ports or VLANs for Faucet
 - Support trunk ports behavior for Faucet
 - Count number of captures triggered in Redis
 - Add default Grafana dashboard that gives Poseidon Stats from Prometheus

# v0.5.9 (2019-05-03)

 - Packaged new version of components, including CRviz v0.2.11 and vent v0.9.0
 - Add support for Ubuntu Disco and removed support for Ubuntu Trusty
 - Cleanup documentation
 - Updated version of pip, cmd2, falcon, mock, and pytest-cov
 - Add new `show version` option in the CLI

# v0.5.8 (2019-04-19)

 - Packaged new versions of components, including poseidonml v0.3.1 and vent v0.8.3
 - Added new options for deleting old captures on a schedule `delete_pcap_files` (defaults to not enabled)
 - Added new fields `controller` and `controller_type`
 - Added flags to the CLI `-nonzero` and `-unique`
 - Fixed some type errors in the CLI
 - Updated versions of pika, pytest, and urllib
 - Moved the CLI from cmd to cmd2, enabling things like Ctrl-r for searching history
 - Added persistent history of commands in the CLI across sessions
 - Added new flag for executing shell commands without going into the shell `poseidon shell -c <command>`
 - Better error checking for invalid flags being passed into commands in the CLI
 - Can now redirect or pipe output of commands in the CLI to any linux command on the system, such as `grep`

# v0.5.7 (2019-04-04)

 - Packaged versions of components, including vent-plugins v0.1.1, poseidonml v0.3.0, crviz v0.2.10, and vent v0.8.2
 - New option `poseidon pcap` is now fully operational
 - Poseidon can now be run without an SDN controller, useful for using the above pcap feature, or looking at an existing Poseidon database
 - Updated version of pika, pytest
 - Log level can now we set on any controller mode including Demo
 - Suppressed error messages on `poseidon stop`
 - Fixed issue where ipv4 and ipv6 addresses from Faucet were getting set to 0
 - Fixed issue where ipv6 columns were not showing up when specified in fields in the CLI

# v0.5.6 (2019-03-22)

 - Updated version of redis, pika, pyyaml, scp, pytest
 - Cleanly shutdown poseidon container on `poseidon stop`
 - Add an experimental `pcap` option to the poseidon command
 - Remove BCF filter rules on poseidon stop and remove any previous filters on start
 - Cleanup BCF response code when calling the API

# v0.5.5 (2019-03-08)

 - Packaged versions of components, including vent-plugins v0.1.0, poseidonml v0.2.9, and vent v0.8.0
 - Fixed role bug in CLI
 - Added more test coverage to get back up to 90%
 - Updated version of pip, pylint
 - Fix crashing bugs in the CLI
 - Made fields and field names consistent in the CLI and the API
 - Added the tool a particular field came from if it wasn't Poseidon directly
 - Can now toggle IPv4 and IPv6 in the CLI

# v0.5.4 (2019-02-22)

 - Updated version of prometheus, pytest, redis, texttable
 - Fixed issues where the shell can crash
 - Changed 'device type' in CLI to 'role'
 - Added 'quit' and 'exit' aliases in the CLI
 - Fixed bug where 'unknown' wasn't getting output correctly in the CLI
 - Fixed multi-word args in the CLI to not use spaces
 - Better help summary in the CLI
 - Add OUI ethernet vendor lookups
 - Add rDNS lookups
 - Add '?' functionality in the CLI
 - Updated the default list of fields in the CLI
 - Split out role and confidence to different fields in the CLI
 - Changed 'UNDEFINED' to 'NO DATA'
 - Updated the CLI commands to have a more intuitive flow

# v0.5.3 (2019-02-08)

 - Updated version of httmock, redis, pip, pytest
 - Ability to build both net and regular poseidon packages easier in Make now
 - Can use the 'all' field sepcifier in the CLI to get all fields
 - Added new configuration option: trust_self_signed_cert which defaults to True
 - Output from external sources such as PoseidonML, p0f, etc. now show results in the CLI
 - Fixed fields of mixed types so they can be used to sort by in the CLI
 - Original header is preserved when overriding fields in CLI
 - Updated and improved documentation for using BCF
 - Fixed an error where results from PoseidonML were sometimes not retrieved
 - Fixed an error where duplicate records were showing up in the CLI
 - Fixed an error where endpoints that were already mirroring superceded queued endpoints
 - `poseidon reset` now clears out the Redis database
 - Fixed port and switch output in the CLI for BCF results
 - Finished implementing specific show commands in the CLI
 - BCF API response codes are now parsed and logged appropriately
 - Action commands in the CLI now work, including changing state and collecting, via changing to say a mirror state
 - Fixed the poseidon shell script to handle if the poseidon-net package was installed
 - Updated Docker images to use alpine 3.9
 - Fixed a serious bug that caused BCF to no longer work with Poseidon due it not being able to create filters by MAC address

# v0.5.2 (2019-01-25)

 - Updated version of pytest, pika, texttable, schedule
 - Added first version of CLI, accessed with `poseidon shell`
 - Can now query endpoint information like what state and when
 - Can now clear out inactive endpoints or ignore specific endpoints
 - Pin pip to a version

# v0.5.1 (2019-01-11)

 - Improved logging output
 - Updated version of gevent, pytest, pytest-cov
 - Made use of sed more stable across platforms
 - Added an additional debian package poseidon-net that is slim and downloads images after installation
 - Ensure that timeout exists in faucet config before trying to remove/change it

# v0.5.0 (2018-12-28)

 - BREAKING CHANGES!
 - Updated Redis key storage - need to clean out redis DB upon upgrade
 - Updated Prometheus labels - need to clean out prometheus DB upon upgrade
 - Updated API with different fields
 - Redis is now updated from Poseidon directly
 - Split out ip address to both ipv4 and ipv6
 - Cleaned up containers on reconfig
 - Poseidon start will recreate images if they were removed
 - Keeps state of endpoints across restarts
 - Actually checks if collector response succeeded or not
 - Only creates a tap if the mirror was successful
 - Fixes issue where changes to the faucet.yaml file weren't taking effect inside the container
 - Added extra transitions for external services changing state of endpoints
 - Prioritizes queued endpoints over reinvestigations
 - Made default_ip more robust when whening more than one
 - Cleaned up API to use standard libraries and reduce duplication
 - Controller updates switch config when an endpoint expires
 - Ignores learn events for endpoints that are already being investigated
 - Cleans up mirrors on restarts
 - Updates Vent to stop captures on expired endpoints
 - All states of endpoints get stored periodically from Poseidon now, so it is consistent

# v0.4.0 (2018-12-14)

 - Updated version of pytest, urllib3, requests, scp, pylint, certifi, redis, prometheus_client
 - Restructred the code base into a more simplified architecture
 - Replaced the custom state machine with pytransitions to make it more reliable
 - Cleaned up logging to be more readable at an INFO level and more useful at a DEBUG level
 - Various bug fixes along the way

# v0.3.6 (2018-10-22)

 - Updated version of pytest, gunicorn, prometheus_client, urllib3, scp, gevent, certifi, requests
 - Fixed a few typos
 - Fixed L2 timeout compared with ARP timeout for Faucet
 - Fixed creation of files/dirs at container start time for volumes
 - Added some developer instructions to the Readme

# v0.3.5 (2018-09-21)

 - Added an inactive state
 - Fixed operating system results from p0f
 - Fixes roles results from PoseidonML
 - Fixed log file creation and rotation

# v0.3.4 (2018-09-10)

 - Updated version of pytest and pytest-cov
 - Fixed the number of endpoints that can be in the mirroring/investigating state
 - Improvements to the logging output
 - Fixed API when learning at L2
 - Reinvestigates if ML results come back with nothing
 - Validates connectivity to the controller before making network_tap requests
 - Reduce connection timeout times
 - Now uses Docker for building Debian package
 - Added reinvestigation_frequency as a configuration option for the Debian package
 - Fix reprompting when using the Debian package with demo and upgrading

# v0.3.3 (2018-08-24)

 - Updated version of certifi, gevent, and pytest
 - Automatically sets timeouts for L2 and L3 for Faucet based on reinvestigation frequency
 - Add api option to poseidon tool
 - Collect and learn at L2 now instead of requiring L3
 - Add timestamps to poseidon.log
 - Improved logging, both poseidon logs and poseidon system-logs exist now

# v0.3.2 (2018-08-10)

 - Updated README
 - Demo now uses cat instead of less
 - Updated version of pytest, prometheus_client, and pylint
 - Improved logging, created a poseidon.log
 - Updated to alpine 3.8

# v0.3.1 (2018-07-27)

 - If span fabric or interface group doesn't exist, don't mirror
 - Updated version of pylint and gevent
 - Improved test coverage
 - Fixed URI for BCF in installer
 - Improved `poseidon start` when forking poseidon
 - Clarity around reconfig rather than configure
 - Fixed learn_public_addresses being set to the wrong type
 - Logged errors with Faucet Connections
 - Improved README

# v0.3.0 (2018-07-13)

 - Deployment now uses a .deb package
 - Fixed the docs builder
 - Fixed issues for missing Faucet files
 - Fix missing keys in metadata for BCF
 - Ensure configured span_fabric and interface_group options exist in BCF
 - Update version of pytest, pyyaml, and prometheus_client
 - Lock Python at 3.6 for gevent
 - Cleaned up and removed old scripts, code, and docs
 - Improved documentation in the README

# v0.2.2 (2018-06-29)

 - Update version of pika, gevent, and pytest
 - Progress on debian package installer and systemd unit
 - Improvements to Travis tests
 - Add healthcheck
 - Cleanup Dockerfile names
 - Fix issues with Poseidon configuring Faucet locally not over SSH
 - Update fixes for Faucet yaml changes
 - Make interface-group configurable for BCF
 - Fix some environment variable issues

# v0.2.1 (2018-06-15)

 - PoseidonML moved to the CyberReboot org
 - Updated version of gevent, pytest, pylint, and requests

# v0.2.0 (2018-06-01)

 - Updated version of pytest
 - Improved test coverage
 - Improve handling environment variables with the helper script
 - Update version of gevent
 - Adds option to ignore learning public ip addresses

# v0.1.9 (2018-05-18)

 - Includes tcprewrite_dot1q in vent startup
 - Fixes subnets for IPv6
 - Updated version of gevent
 - Publishes specific port for Prometheus
 - Properly converts IPv6 to an int for Prometheus
 - Updated version of scp
 - Updated version of pylint

# v0.1.8 (2018-05-04)

 - Add metrics to Prometheus
 - Allow span-fabric name to be configured
 - Update pytest version
 - Update gunicorn version
 - Update API version of Alpine Linux
 - Add additional metadata for active or inactive (expired hosts)
 - Stores state changes to external systems (Vent)
 - Includes an additional endpoint to the API for extra details of the network (/network_full)
 - When unmirroring, it ensures that all captures on that port are finished first
 - Listens to FAUCET PORT_CHANGE and L2_EXPIRE events now
 - Updates known endpoints when they go away

# v0.1.7 (2018-04-06)

 - Improved mac learning
 - Improved logging
 - Log additional FAUCET Events
 - Fix mirroring and unmirroring for FAUCET

# v0.1.6 (2018-03-23)

 - Updates FAUCET paths to conform with 1.7.x
 - Adds an API for getting endpoints that Poseidon knows about
 - Updates a number of dependency versions
 - Adds CRviz for visualizing the network that Poseidon knows about
 - Fixes some bugs with mirroring
 - Fixes a bug where null would get written to faucet.yaml
 - FAUCET mirroring now uses messages from Events rather than logs
 - FAUCET can now unmirror

# v0.1.5 (2018-03-09)

 - Adds support for RabbitMQ events from FAUCET
 - Allows queue to not be exclusive
 - Improve mirroring ports to allow for multiple mirrors simultaneously
 - Fixes feedback and gets out of mirroring when appropriate
 - Includes p0f in the helper script
 - Fixes a change in the formatting of the FAUCET log file
 - Slightly better error checking for environment variables

# v0.1.4 (2018-02-09)

 - Updated versions for dependencies

# v0.1.3 (2018-01-26)

 - Quoted controller_mirror_ports to allow for special characters
 - Fixed mirroring for FAUCET
 - Better error checking for the helper script
 - Clarify some documentation
 - Set defaults for log and config files for FAUCET

# v0.1.2 (2018-01-12)

 - Fixed bug where mirroring was backwards for FAUCET (thanks @alshaboti)
 - Improved the helper run script to be easier
 - Removed Elasticsearch and RMQ-to-ES containers from Vent build and runtime for Poseidon

# v0.1.1 (2017-12-15)

 - New feature if poseidon and faucet on the same host, doesn't require ssh/scp
 - Various bug fixes

# v0.1.0 (2017-12-04)

 - Initial release
 - Basic functionality with Big Cloud Fabric and FAUCET controllers
 - Can be run as a standalone Docker container or orchestrated through Vent.
