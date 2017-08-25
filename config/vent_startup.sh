#!/bin/bash
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#	Script for configuring vcontrol setup with a single vent instance named
#   vent.example.
#	Dependencies:
# 		git clone http://github.com/CyberReboot/vcontrol.git
#	 	cd vcontrol/
# 		make api
#		export VCONTROL_DAEMON=http://localhost:<port from docker container>
#		pip install vcontrol
# 		vcontrol version  # verifies installation and setup of vcontrol
#		docker exec -it vcontrol-daemon vcontrol providers add <provider name> "<options>"
#
vcontrol machines create vent.example $VENT_PROVIDER
# edit poseidon plugin templates
vcontrol plugins add vent.example http://github.com/lanhamt/poseidon.git
vcontrol commands deploy vent.example $POSEIDON_REPO_PATH/templates/features.template
vcontrol commands deploy vent.example $POSEIDON_REPO_PATH/templates/heuristics.template
vcontrol commands deploy vent.example $POSEIDON_REPO_PATH/templates/deep_algos.template
vcontrol commands deploy vent.example $POSEIDON_REPO_PATH/templates/ml_algos.template
vcontrol commands build vent.example all
vcontrol commands build vent.example all
vcontrol commands start vent.example all
vcontrol commands start vent.example all
# builds all images - takes a while
vcontrol commands clean vent.example all
vcontrol commands start vent.example core
vcontrol commands start vent.example passive
# make rest call to start collector
