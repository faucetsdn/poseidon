FROM python:3.11-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1

COPY . /poseidon
WORKDIR /poseidon

ENV PATH="${PATH}:/root/.local/bin"
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc git g++ libev-dev libyaml-dev tini && \
  curl -sSL https://install.python-poetry.org | python3 - --version 1.1.15 && \
  poetry config virtualenvs.create false && \
  cd lib/poseidon_api && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  cd lib/poseidon_cli && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  cd lib/poseidon_core && poetry run pip install 'setuptools==64.0.3' && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  apt-get purge -y gcc g++ && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:9304/ || exit 1

RUN mkdir -p /opt/poseidon
RUN mv /poseidon/config/poseidon.config /opt/poseidon/poseidon.config
ENV POSEIDON_CONFIG /opt/poseidon/poseidon.config

CMD tini -s -- poseidon-core
