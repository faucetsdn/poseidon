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
