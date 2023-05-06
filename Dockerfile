FROM python:3.10-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1
ENV PATH="${PATH}:/root/.local/bin"
ENV POSEIDON_CONFIG /opt/poseidon/poseidon.config

COPY . /poseidon
WORKDIR /poseidon

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | python3 - --version 1.4.2 && \
    poetry config virtualenvs.create false && \
    apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

WORKDIR /poseidon/lib/poseidon_cli
RUN poetry install --no-interaction --no-ansi && poetry build
WORKDIR /poseidon/lib/poseidon_core
RUN apt-get update && apt-get install -y --no-install-recommends gcc git g++ libev-dev libyaml-dev tini && \
    poetry run pip install 'setuptools==64.0.3' && poetry install --no-interaction --no-ansi && poetry build && \
    apt-get purge -y gcc g++ && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*
WORKDIR /poseidon/lib/poseidon_api
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && \
    poetry install --no-interaction --no-ansi && poetry build && \
    apt-get purge -y gcc g++ && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:9304/ || exit 1

WORKDIR /opt/poseidon
RUN mv /poseidon/config/poseidon.config /opt/poseidon/poseidon.config

WORKDIR /poseidon
CMD tini -s -- poseidon-core
