FROM ubuntu:latest

LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

RUN apt-get update && apt-get install -y python3 python3-pip

RUN pip3 install Sphinx==1.4
RUN pip3 install sphinx_rtd_theme
RUN pip3 install alabaster
RUN pip3 install sphinx_bootstrap_theme
RUN pip3 install recommonmark

ENV PYTHONUNBUFFERED 0
EXPOSE 8080:8080

COPY . /poseidonWork
WORKDIR /poseidonWork
ENV PYTHONPATH /poseidonWork/poseidon:$PYTHONPATH
ENV POSEIDON_CONFIG /poseidonWork/config/poseidon.config

# install dependencies of poseidon modules for poseidon
RUN find . -name requirements.txt -type f -exec pip3 install -r {} \;
RUN sphinx-apidoc -o docs/source poseidon -F --follow-links && cd docs/source && make html && make man

WORKDIR /poseidonWork/docs/source/_build/html

CMD ["/usr/bin/python3","-m","http.server","8080"]
