SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -t $(TAG) .

run_tests: build_poseidon
	docker kill $(TAG)-redis || true
	docker build -f ./Dockerfile.test -t $(TAG)-test .
	docker run --rm -d --name $(TAG)-redis redis:latest
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock --link $(TAG)-redis:redis -it $(TAG)-test
	docker kill $(TAG)-redis

.PHONY:  build_poseidon run_tests
