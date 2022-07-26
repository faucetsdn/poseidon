FROM python:3.10-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1

COPY . /poseidon
WORKDIR /poseidon

ENV PATH="${PATH}:/root/.poetry/bin"
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc git g++ libev-dev libyaml-dev tini && \
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - && \
  poetry config virtualenvs.create false && \
  cd lib/poseidon_api && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  cd lib/poseidon_cli && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  cd lib/poseidon_core && poetry install --no-interaction --no-ansi && poetry build && cd ../../ && \
  apt-get purge -y gcc g++ && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:9304/ || exit 1

RUN mkdir -p /opt/poseidon
RUN mv /poseidon/config/poseidon.config /opt/poseidon/poseidon.config
ENV POSEIDON_CONFIG /opt/poseidon/poseidon.config

CMD tini -s -- poseidon-core
