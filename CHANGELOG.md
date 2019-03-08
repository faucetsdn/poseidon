# v0.5.5 (2019-03-08)

 - Packaged versions of components, including vent-plugins v0.1.0, posiedonml v0.2.9, and vent v0.8.0
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
 - Fixed a serious bug that cause BCF to no longer work with Poseidon due it not being able to create filters by MAC address

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
