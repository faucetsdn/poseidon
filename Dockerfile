FROM python:3.9-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1
COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck

RUN apt-get update && apt-get install -y curl gcc g++ tini libyaml-dev && \
  pip3 install --no-cache-dir -r requirements.txt && \
  pip3 install --no-cache-dir -r /healthcheck/requirements.txt && \
  apt-get purge -y gcc g++ python3-dev && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /poseidon
WORKDIR /poseidon
ENV PYTHONPATH /poseidon:$PYTHONPATH
RUN mkdir -p /opt/poseidon
RUN mv /poseidon/config/poseidon.config /opt/poseidon/poseidon.config
ENV POSEIDON_CONFIG /opt/poseidon/poseidon.config

CMD (flask run > /dev/null 2>&1) & (tini -s -- /usr/local/bin/python3 poseidon/main.py)
