SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -f ./Dockerfile.poseidon -t $(TAG) .

run_poseidon: build_poseidon
	docker run --rm -it $(TAG)

run_dev:
	docker run --rm -v "$(shell pwd):/poseidonWork" -it $(TAG)

run_sh: build_poseidon
	docker run --rm -it --entrypoint sh $(TAG)

build_docs:
	docker build -f ./Dockerfile.docs -t $(TAG)-docs .

run_docs: build_docs
	docker run --rm -it -p 8080 $(TAG)-docs

run_tests: build_poseidon
	docker build -f ./Dockerfile.test -t $(TAG)-test .
	docker run --rm -d --name $(TAG)-redis redis:latest
	docker run --rm --link $(TAG)-redis:redis -it $(TAG)-test
	docker kill $(TAG)-redis

build_debian:
	mkdir -p installers/debian/$(TAG)-$(VERSION)/DEBIAN
	cp installers/debian/control installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/postinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/preinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/prerm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/templates installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	mkdir -p installers/debian/$(TAG)-$(VERSION)/opt/poseidon
	mkdir -p installers/debian/$(TAG)-$(VERSION)/usr/bin
	mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/systemd/system
	cp installers/debian/poseidon.service installers/debian/$(TAG)-$(VERSION)/etc/systemd/system/
	cp -R !(installers) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	mkdir -p dist
	dpkg-deb --build installers/debian/$(TAG)-$(VERSION)
	mv installers/debian/*.deb dist/
	rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian

.PHONY:  build_debian build_installers build_poseidon run_poseidon run_sh build_docs run_docs run_tests
