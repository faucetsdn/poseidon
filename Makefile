run: clean depends build docs
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		echo "No DOCKER_HOST environment variable set."; \
		exit 1; \
	fi; \
	docker run --name poseidon-api -dP poseidon-api; \
	port=$$(docker port poseidon-api 8080/tcp | sed 's/^.*://'); \
	api_url=$$docker_url:$$port; \
	docker run --name poseidon -dP -e ALLOW_ORIGIN=$$api_url poseidon; \
	port=$$(docker port poseidon 8000/tcp | sed 's/^.*://'); \
	poseidon_url=$$docker_url:$$port; \
	echo; \
	echo "The API can be accessed here: $$api_url"; \
	echo "Poseidon can be accessed here: $$poseidon_url"; \
	echo

test: build

docs: clean-docs build
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		echo "No DOCKER_HOST environment variable set."; \
		exit 1; \
	fi; \
	docker run --name poseidon-docs -w /poseidon/docs/_build/html -Pd --entrypoint "python" poseidon -m SimpleHTTPServer; \
	port=$$(docker port poseidon-docs 8000/tcp | sed 's/^.*://'); \
	doc_url=$$docker_url:$$port; \
	echo; \
	echo "The docs can be accessed here: $$doc_url"; \
	echo

build: depends
	cd api && docker build -t poseidon-api .
	docker build -t poseidon .

clean-all: clean depends
	@docker rmi poseidon
	@docker rmi poseidon-api

clean-docs: depends
	@docker ps -aqf "name=poseidon-docs" | xargs docker rm -f

clean: clean-docs depends
	@docker ps -aqf "name=poseidon" | xargs docker rm -f
	@docker ps -aqf "name=poseidon-api" | xargs docker rm -f

depends:
	@echo
	@echo "checking dependencies"
	@echo
	docker -v

.PHONY: run test docs build clean clean-all clean-docs depends
