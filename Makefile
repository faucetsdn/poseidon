SHELL:=/bin/bash -O extglob -c
TAG=poseidon
VERSION=$(shell cat VERSION)

build_poseidon:
	docker build -t $(TAG) .

build_docs:
	docker build -f ./Dockerfile.docs -t $(TAG)-docs .

run_docs: build_docs
	docker run --rm -it -p 8080 $(TAG)-docs

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
	cp -R !(installers) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .dockerignore installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:latest
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:latest
	docker pull cyberreboot/vent-file-drop:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-file-drop.tar cyberreboot/vent-file-drop:master
	docker pull cyberreboot/vent-network-tap:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-network-tap.tar cyberreboot/vent-network-tap:master
	docker pull cyberreboot/vent-rabbitmq:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rabbitmq.tar cyberreboot/vent-rabbitmq:master
	docker pull cyberreboot/vent-redis:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-redis.tar cyberreboot/vent-redis:master
	docker pull cyberreboot/vent-rq-dashboard:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-dashboard.tar cyberreboot/vent-rq-dashboard:master
	docker pull cyberreboot/vent-rq-worker:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-worker.tar cyberreboot/vent-rq-worker:master
	docker pull cyberreboot/vent-syslog:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-syslog.tar cyberreboot/vent-syslog:master
	docker pull cyberreboot/poseidon-api:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidon-api.tar cyberreboot/poseidon-api:master
	docker pull cyberreboot/vent-plugins-pcap-to-node-pcap:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-pcap-to-node-pcap.tar cyberreboot/vent-plugins-pcap-to-node-pcap:master
	docker pull cyberreboot/vent-plugins-p0f:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-p0f.tar cyberreboot/vent-plugins-p0f:master
	docker pull cyberreboot/vent-plugins-tcprewrite-dot1q:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-tcprewrite-dot1q.tar cyberreboot/vent-plugins-tcprewrite-dot1q:master
	docker pull cyberreboot/crviz:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-crviz.tar cyberreboot/crviz:master
	docker pull cyberreboot/poseidonml:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidonml.tar cyberreboot/poseidonml:master
	docker pull cyberreboot/poseidon:master
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidon.tar cyberreboot/poseidon:master
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
	cp -R !(installers) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .dockerignore installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:latest
	docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:latest
	mkdir -p dist
	docker build -t poseidon-dpkg -f Dockerfile.dpkg .
	docker run --rm poseidon-dpkg > dist/$(TAG)-$(VERSION)-net.deb
	rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian build_debian_net

.PHONY:  build_debian build_installers build_poseidon build_docs run_docs run_tests
