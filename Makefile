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
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/DEBIAN
	sudo cp installers/debian/control installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/postinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/preinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/prerm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/postrm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/templates installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/opt/poseidon
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/usr/bin
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/systemd/system
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/poseidon
	sudo cp installers/debian/poseidon.service installers/debian/$(TAG)-$(VERSION)/etc/systemd/system/
	sudo cp installers/debian/default.conf installers/debian/$(TAG)-$(VERSION)/etc/poseidon/
	sudo cp -R !(installers) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	sudo mkdir -p dist
	sudo dpkg-deb --build installers/debian/$(TAG)-$(VERSION)
	sudo mv installers/debian/*.deb dist/
	sudo rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian

.PHONY:  build_debian build_installers build_poseidon run_poseidon run_sh build_docs run_docs run_tests
