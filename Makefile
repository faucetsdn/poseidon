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
	docker build -f ./Dockerfile.test -t $(TAG)-test .
	docker run --rm -d --name $(TAG)-redis redis:latest
	docker run --rm --link $(TAG)-redis:redis -it $(TAG)-test
	docker kill $(TAG)-redis

build_debian:
	sudo rm -rf dist
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/DEBIAN
	sudo cp installers/debian/config installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/control installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/postinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/preinst installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/prerm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/postrm installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo cp installers/debian/templates installers/debian/$(TAG)-$(VERSION)/DEBIAN/
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/usr/bin
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/systemd/system
	sudo mkdir -p installers/debian/$(TAG)-$(VERSION)/etc/poseidon
	sudo cp installers/debian/poseidon.service installers/debian/$(TAG)-$(VERSION)/etc/systemd/system/
	sudo cp installers/debian/default.conf installers/debian/$(TAG)-$(VERSION)/etc/poseidon/
	sudo cp -R !(installers) installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp .dockerignore installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp .plugin_config.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp .vent_startup.yml installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp -R .git installers/debian/$(TAG)-$(VERSION)/opt/poseidon/
	sudo cp -R bin/* installers/debian/$(TAG)-$(VERSION)/usr/bin/
	docker pull cyberreboot/vent:latest
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent.tar cyberreboot/vent:latest
	docker pull cyberreboot/vent-file-drop:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-file-drop.tar cyberreboot/vent-file-drop:master
	docker pull cyberreboot/vent-network-tap:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-network-tap.tar cyberreboot/vent-network-tap:master
	docker pull cyberreboot/vent-rabbitmq:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rabbitmq.tar cyberreboot/vent-rabbitmq:master
	docker pull cyberreboot/vent-redis:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-redis.tar cyberreboot/vent-redis:master
	docker pull cyberreboot/vent-rq-dashboard:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-dashboard.tar cyberreboot/vent-rq-dashboard:master
	docker pull cyberreboot/vent-rq-worker:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-rq-worker.tar cyberreboot/vent-rq-worker:master
	docker pull cyberreboot/vent-syslog:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-syslog.tar cyberreboot/vent-syslog:master
	docker pull cyberreboot/poseidon-api:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidon-api.tar cyberreboot/poseidon-api:master
	docker pull cyberreboot/vent-plugins-pcap-to-node-pcap:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-pcap-to-node-pcap.tar cyberreboot/vent-plugins-pcap-to-node-pcap:master
	docker pull cyberreboot/vent-plugins-p0f:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-p0f.tar cyberreboot/vent-plugins-p0f:master
	docker pull cyberreboot/vent-plugins-tcprewrite-dot1q:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-vent-plugins-tcprewrite-dot1q.tar cyberreboot/vent-plugins-tcprewrite-dot1q:master
	docker pull cyberreboot/crviz:master
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-crviz.tar cyberreboot/crviz:master
	docker pull cyberreboot/poseidonml:base
	sudo docker save -o installers/debian/$(TAG)-$(VERSION)/opt/poseidon/dist/cyberreboot-poseidonml.tar cyberreboot/poseidonml:base
	sudo mkdir -p dist
	sudo dpkg-deb --build installers/debian/$(TAG)-$(VERSION)
	sudo mv installers/debian/*.deb dist/
	sudo rm -rf installers/debian/$(TAG)-$(VERSION)

build_installers: build_debian

.PHONY:  build_debian build_installers build_poseidon build_docs run_docs run_tests
