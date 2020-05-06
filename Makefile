SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -t $(TAG) .

run_tests: build_poseidon
	docker build -f ./Dockerfile.test -t $(TAG)-test .
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock $(TAG)-test

.PHONY:  build_poseidon run_tests
