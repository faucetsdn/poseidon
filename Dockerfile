FROM alpine:3.10
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    build-base \
    curl \
    python3 \
    python3-dev \
    py3-paramiko \
    tini \
    yaml-dev && \
    pip3 install --no-cache-dir --upgrade pip==19.1 && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir -r /healthcheck/requirements.txt && \
    apk del build-base \
    python3-dev \
    yaml-dev && \
    rm -rf /var/cache/* && \
    rm -rf /root/.cache/*

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /poseidon
WORKDIR /poseidon
ENV PYTHONPATH /poseidon/poseidon:$PYTHONPATH
ENV POSEIDON_CONFIG /poseidon/config/poseidon.config

ENV PYTHONUNBUFFERED 0
ENV SYS_LOG_HOST NOT_CONFIGURED
ENV SYS_LOG_PORT 514

EXPOSE 9304

CMD (flask run > /dev/null 2>&1) & (tini -s -- /usr/bin/python3 /poseidon/poseidon/main.py)
