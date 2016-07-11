run: clean depends build docs notebooks main api monitor storage printPlaces periodically
printPlaces:
	@docker ps --format "table {{.Names}}\thttp://{{.Ports}}" |sed 's/0.0.0.0/localhost/' | sed 's/->/ container:/'

periodically: clean-periodically build-periodically
	docker run --net=container:poseidon-monitor periodically

api: clean-api build-api
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		if [ ! -z "${DOCKERFORMAC}" ]; then \
			docker_url=http://127.0.0.1; \
		else \
			echo "No DOCKER_HOST environment variable set."; \
			exit 1; \
		fi; \
	fi; \
	docker run --name poseidon-api -dP poseidon-api ; \
	portApi=$$(docker port poseidon-api 8080/tcp | sed 's/^.*://'); \
	api_url=$$docker_url:$$portApi; \
	echo "The API can be accessed here: $$api_url"; \
	echo

test: build

main: clean-main build-main
	docker run --name poseidon-main -it poseidon-main

storage: clean-storage build-storage
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=$$docker_host; \
	else \
		if [ ! -z "${DOCKERFORMAC}" ]; then \
			docker_url=localhost; \
		else \
			echo "No DOCKER_HOST environment variable set."; \
			exit 1; \
		fi; \
	fi; \
	docker run --name poseidon-storage -dp 27017:27017 mongo >/dev/null; \
	port=$$(docker port poseidon-storage 27017/tcp | sed 's/^.*://'); \
	echo "poseidon-storage can be accessed here: $$docker_url:$$port"; \
	echo

monitor: storage api clean-monitor build-monitor
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		if [ ! -z "${DOCKERFORMAC}" ]; then \
		docker_url=http://localhost; \
		else \
			echo "No DOCKER_HOST environment variable set."; \
			exit 1; \
		fi; \
	fi; \
	portApi=$$(docker port poseidon-api 8080/tcp | sed 's/^.*://'); \
	docker run --name poseidon-monitor -dp 8555:8000 -e ALLOW_ORIGIN=$$docker_url:$$portApi poseidon-monitor ; \
	port=$$(docker port poseidon-monitor 8000/tcp | sed 's/^.*://'); \
	echo "poseidon-monitor can be accessed here: $$docker_url:$$port"; \
	echo

notebooks: clean-notebooks build-notebooks
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		if [ ! -z "${DOCKERFORMAC}" ]; then \
			docker_url=http://localhost; \
		else \
			echo "No DOCKER_HOST environment variable set."; \
			exit 1; \
		fi; \
	fi; \
	docker run --name poseidon-notebooks -w /notebooks -dP -v "$$(pwd):/notebooks" poseidon-notebooks jupyter notebook --ip=0.0.0.0 --no-browser >/dev/null; \
	port=$$(docker port poseidon-notebooks 8888/tcp | sed 's/^.*://'); \
	notebook_url=$$docker_url:$$port; \
	echo "The notebooks can be accessed here: $$notebook_url"

docs: clean-docs build
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		if [ ! -z "${DOCKERFORMAC}" ]; then \
			docker_url=http://localhost; \
		else \
			echo "No DOCKER_HOST environment variable set."; \
			exit 1; \
		fi; \
	fi; \
	docker run --name poseidon-docs -dP poseidon-docs; \
	port=$$(docker port poseidon-docs 8000/tcp | sed 's/^.*://'); \
	doc_url=$$docker_url:$$port; \
	echo; \
	echo "The docs can be accessed here: $$doc_url"

build: depends
	# docker-compose build 
	docker build -t poseidon-notebooks -f Dockerfile.notebooks .
	docker build -t poseidon-monitor  -f Dockerfile.monitor .
	docker build -t poseidon-main  -f Dockerfile.main .

build-periodically:
	docker build -t periodically -f Dockerfile.periodically .

build-api:
	cd api && docker build -t poseidon-api .

build-docs:
	docker build -t poseidon-docs -f Dockerfile.docs .

build-monitor:
	docker build -t poseidon-monitor -f Dockerfile.monitor .

build-notebooks:
	docker build -t poseidon-notebooks -f Dockerfile.notebooks .

build-main:
	docker build -t poseidon-main  -f Dockerfile.main .

build-storage:
	docker pull mongo

clean-all: clean depends
	@docker rmi poseidon-monitor
	@docker rmi poseidon-storagmain
	@docker rmi poseidon-main
	@docker rmi poseidon-api
	@docker rmi periodically

clean-periodically: depends
	@docker ps -afq "name=periodically" | xargs docker rm -f

clean-storage: depends
	@docker ps -aqf "name=poseidon-storage" | xargs docker rm -f

clean-monitor: depends
	@docker ps -aqf "name=poseidon-monitor" | xargs docker rm -f

clean-main: depends
	@docker ps -aqf "name=poseidon-main" | xargs docker rm -f

clean-docs: depends
	@docker ps -aqf "name=poseidon-docs" | xargs docker rm -f

clean-api: depends
	@docker ps -aqf "name=poseidon-api" | xargs docker rm -f

clean-notebooks: depends
	@docker ps -aqf "name=poseidon-notebooks" | xargs docker rm -f

clean: clean-docs clean-notebooks depends
	#@docker ps -aqf "name=poseidon" | xargs docker rm -f
	#@docker ps -aqf "name=poseidon-api" | xargs docker rm -f

depends:
	@echo
	@echo "checking dependencies"
	@echo
	docker -v

.PHONY: run test docs build notebooks clean clean-all clean-notebooks clean-docs depends
