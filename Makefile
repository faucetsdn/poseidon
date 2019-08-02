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
	cp .dockerignore installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:v0.9.6
	
	docker pull poseidon/poseidon:v0.6.5
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/poseidon-poseidon.tar poseidon/poseidon:v0.6.5
	docker pull networkml/networkml:v0.3.5
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/networkml-networkml.tar networkml/networkml:v0.3.5
	docker pull vent/vent-file-drop:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-file-drop.tar vent/vent-file-drop:v0.9.6
	docker pull vent/vent-rabbitmq:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-rabbitmq.tar vent/vent-rabbitmq:v0.9.6
	docker pull vent/vent-syslog:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-syslog.tar vent/vent-syslog:v0.9.6
	docker pull vent-plugins/vent-plugins-pcap-to-node-pcap:v0.1.2
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-plugins-vent-plugins-pcap-to-node-pcap.tar vent-plugins/vent-plugins-pcap-to-node-pcap:v0.1.2
	docker pull vent/vent-rq-worker:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-rq-worker.tar vent/vent-rq-worker:v0.9.6
	docker pull vent/vent-network-tap:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-network-tap.tar vent/vent-network-tap:v0.9.6
	docker pull crviz/crviz:v0.3.8
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/crviz-crviz.tar crviz/crviz:v0.3.8
	docker pull poseidon/poseidon-api:v0.6.5
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/poseidon-poseidon-api.tar poseidon/poseidon-api:v0.6.5
	docker pull vent-plugins/vent-plugins-tcprewrite-dot1q:v0.1.2
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-plugins-vent-plugins-tcprewrite-dot1q.tar vent-plugins/vent-plugins-tcprewrite-dot1q:v0.1.2
	docker pull vent/vent-redis:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-redis.tar vent/vent-redis:v0.9.6
	docker pull vent/vent-rq-dashboard:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-vent-rq-dashboard.tar vent/vent-rq-dashboard:v0.9.6
	docker pull vent-plugins/vent-plugins-p0f:v0.1.2
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/vent-plugins-vent-plugins-p0f.tar vent-plugins/vent-plugins-p0f:v0.1.2
	
	mkdir -p dist
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
	cp .dockerignore installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:v0.9.6
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:v0.9.6
	
	mkdir -p dist
	docker build -t poseidon-dpkg --build-arg PKG_NAME=poseidon-net -f Dockerfile.dpkg .
	docker run --rm poseidon-dpkg > dist/$(TAG)-$(VERSION)-net.deb
	rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian build_debian_net

.PHONY:  build_debian build_installers build_poseidon run_tests
