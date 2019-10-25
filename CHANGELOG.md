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
