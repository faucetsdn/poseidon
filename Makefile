run: depends build
	docker run --name poseidon -dP poseidon

test: build

docs: build
	docker run --name poseidon-docs -w /poseidon/docs/_build/html -Pd --entrypoint "python" poseidon -m SimpleHTTPServer

build: depends
	docker build -t poseidon .

clean: depends
	docker ps -aqf "name=poseidon" | xargs docker rm -f
	docker ps -aqf "name=poseidon-docs" | xargs docker rm -f
	docker rmi poseidon

depends:
	@echo
	@echo "checking dependencies"
	@echo
	docker -v

.PHONY: run test docs build clean depends
