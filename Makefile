run: clean depends build docs notebooks
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		echo "No DOCKER_HOST environment variable set."; \
		exit 1; \
	fi; \
	docker run --name poseidon-api -dP poseidon-api >/dev/null; \
	port=$$(docker port poseidon-api 8080/tcp | sed 's/^.*://'); \
	api_url=$$docker_url:$$port; \
	docker run --name poseidon-rest -dP -e ALLOW_ORIGIN=$$api_url poseidon-rest >/dev/null; \
	port=$$(docker port poseidon-rest 8000/tcp | sed 's/^.*://'); \
	poseidon_url=$$docker_url:$$port; \
	echo "The API can be accessed here: $$api_url"; \
	echo "poseidon-rest can be accessed here: $$poseidon_url"; \
	echo

test: build

notebooks: clean-notebooks build
	@ if [ ! -z "${DOCKER_HOST}" ]; then \
		docker_host=$$(env | grep DOCKER_HOST | cut -d':' -f2 | cut -c 3-); \
		docker_url=http://$$docker_host; \
	else \
		echo "No DOCKER_HOST environment variable set."; \
		exit 1; \
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
		echo "No DOCKER_HOST environment variable set."; \
		exit 1; \
	fi; \
	docker run --name poseidon-docs -w /poseidon/docs/_build/html -dP --entrypoint "python" poseidon-rest -m SimpleHTTPServer >/dev/null; \
	port=$$(docker port poseidon-docs 8000/tcp | sed 's/^.*://'); \
	doc_url=$$docker_url:$$port; \
	echo; \
	echo "The docs can be accessed here: $$doc_url"

build: depends
	cd api && docker build -t poseidon-api .
	docker build -t poseidon-notebooks -f Dockerfile.notebooks .
	docker build -t poseidon-rest  -f Dockerfile.rest .

clean-all: clean depends
	@docker rmi poseidon-rest
	@docker rmi poseidon-api

clean-docs: depends
	@docker ps -aqf "name=poseidon-docs" | xargs docker rm -f

clean-notebooks: depends
	@docker ps -aqf "name=poseidon-notebooks" | xargs docker rm -f

clean: clean-docs clean-notebooks depends
	@docker ps -aqf "name=poseidon" | xargs docker rm -f
	@docker ps -aqf "name=poseidon-api" | xargs docker rm -f

depends:
	@echo
	@echo "checking dependencies"
	@echo
	docker -v

.PHONY: run test docs build notebooks clean clean-all clean-notebooks clean-docs depends
