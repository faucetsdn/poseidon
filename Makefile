SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -t $(TAG) .

.PHONY:  build_poseidon
