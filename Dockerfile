FROM python:3.9-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1
COPY src/core/requirements.txt core-requirements.txt
COPY src/api/requirements.txt api-requirements.txt
COPY src/cli/requirements.txt cli-requirements.txt
COPY workers/requirements.txt workers-requirements.txt
COPY healthcheck /healthcheck

RUN apt-get update && apt-get install -y --no-install-recommends curl gcc git g++ tini libev-dev libyaml-dev && \
  python3 -m pip install -U pip && \
  pip3 install --no-cache-dir --upgrade setuptools && \
  pip3 install --no-cache-dir -r core-requirements.txt && \
  pip3 install --no-cache-dir -r api-requirements.txt && \
  pip3 install --no-cache-dir -r cli-requirements.txt && \
  pip3 install --no-cache-dir -r workers-requirements.txt && \
  pip3 install --no-cache-dir -r /healthcheck/requirements.txt && \
  apt-get purge -y gcc g++ && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /poseidon
WORKDIR /poseidon/src/core
RUN python3 setup.py sdist install
WORKDIR /poseidon/src/cli
RUN python3 setup.py sdist install
WORKDIR /poseidon/src/api
RUN python3 setup.py sdist install
RUN mkdir -p /opt/poseidon
RUN mv /poseidon/config/poseidon.config /opt/poseidon/poseidon.config
WORKDIR /poseidon
ENV POSEIDON_CONFIG /opt/poseidon/poseidon.config

CMD (flask run > /dev/null 2>&1) & (tini -s -- poseidon-core)
