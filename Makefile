SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -t $(TAG) .

run_tests: build_poseidon
	docker kill $(TAG)-redis || true
	docker build -f ./Dockerfile.test -t $(TAG)-test .
	docker run --rm -d --name $(TAG)-redis redis:latest
	docker run --rm --link $(TAG)-redis:redis -it $(TAG)-test
	docker kill $(TAG)-redis

build_debian:
	mkdir -p installers/debian/$(TAG)-$(VERSION)/DEBIAN
	cp installers/debian/config installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/control installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/postinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/preinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/prerm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/postrm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/templates installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	mkdir -p installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist
	mkdir -p installers/debian/$(TAG)-$(VERSION)/usr/bin
	mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/systemd/system
	mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/poseidon
	cp installers/debian/poseidon.service installers/debian/$(TAG)-$(VERSION)/etc/systemd/system/
	cp installers/debian/default.conf installers/debian/$(TAG)-$(VERSION)/etc/poseidon/
	cp -R !(installers|dist) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:v0.10.1

	docker pull cyberreboot/vent-file-drop:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-file-drop.tar cyberreboot/vent-file-drop:v0.10.1
	docker pull cyberreboot/vent-network-tap:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-network-tap.tar cyberreboot/vent-network-tap:v0.10.1
	docker pull cyberreboot/vent-rabbitmq:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rabbitmq.tar cyberreboot/vent-rabbitmq:v0.10.1
	docker pull cyberreboot/vent-redis:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-redis.tar cyberreboot/vent-redis:v0.10.1
	docker pull cyberreboot/vent-rq-dashboard:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-dashboard.tar cyberreboot/vent-rq-dashboard:v0.10.1
	docker pull cyberreboot/vent-rq-worker:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-worker.tar cyberreboot/vent-rq-worker:v0.10.1
	docker pull cyberreboot/vent-syslog:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-syslog.tar cyberreboot/vent-syslog:v0.10.1
	docker pull cyberreboot/poseidon:v0.8.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidon.tar cyberreboot/poseidon:v0.8.1
	docker pull cyberreboot/poseidon-api:v0.8.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidon-api.tar cyberreboot/poseidon-api:v0.8.1
	docker pull cyberreboot/vent-plugins-pcap-to-node-pcap:v0.1.7
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-pcap-to-node-pcap.tar cyberreboot/vent-plugins-pcap-to-node-pcap:v0.1.7
	docker pull cyberreboot/vent-plugins-p0f:v0.1.7
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-p0f.tar cyberreboot/vent-plugins-p0f:v0.1.7
	docker pull cyberreboot/vent-plugins-tcprewrite-dot1q:v0.1.7
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-tcprewrite-dot1q.tar cyberreboot/vent-plugins-tcprewrite-dot1q:v0.1.7
	docker pull cyberreboot/crviz:v0.3.17
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-crviz.tar cyberreboot/crviz:v0.3.17
	docker pull cyberreboot/networkml:v0.4.4
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-networkml.tar cyberreboot/networkml:v0.4.4

	mkdir -p dist
	rm -rf dist/*
	docker build -t poseidon-dpkg -f Dockerfile.dpkg .
	docker run --rm poseidon-dpkg > dist/$(TAG)-$(VERSION).deb
	rm -rf installers/debian/$(TAG)-$(VERSION)

build_debian_net:
	mkdir -p installers/debian/$(TAG)-$(VERSION)/DEBIAN
	cp installers/debian/config installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/control installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/postinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/preinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/prerm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/postrm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	cp installers/debian/templates installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	mkdir -p installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist
	mkdir -p installers/debian/$(TAG)-$(VERSION)/usr/bin
	mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/systemd/system
	mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/poseidon
	cp installers/debian/poseidon.service installers/debian/$(TAG)-$(VERSION)/etc/systemd/system/
	cp installers/debian/default.conf installers/debian/$(TAG)-$(VERSION)/etc/poseidon/
	cp -R !(installers|dist) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:v0.10.1
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:v0.10.1

	mkdir -p dist
	docker build -t poseidon-dpkg --build-arg PKG_NAME=poseidon-net -f Dockerfile.dpkg .
	docker run --rm poseidon-dpkg > dist/$(TAG)-$(VERSION)-net.deb
	rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian build_debian_net

.PHONY:  build_debian build_installers build_poseidon run_tests
