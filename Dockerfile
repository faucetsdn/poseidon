FROM alpine:3.12
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="primary"

ENV PYTHONUNBUFFERED 1
COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    build-base \
    curl \
    go \
    git \
    linux-headers \
    python3 \
    py3-pip \
    python3-dev \
    py3-paramiko \
    tini \
    yaml-dev && \
    pip3 install --no-cache-dir -r requirements.txt -r /healthcheck/requirements.txt && \
    apk del build-base \
    python3-dev \
    yaml-dev && \
    rm -rf /var/cache/* && \
    rm -rf /root/.cache/*
ENV GNMIREPO=github.com/google/gnxi
ENV GOPATH=/root/go
RUN mkdir -p $GOPATH && for tool in capabilities get set target; do toolrepo=$GNMIREPO/gnmi_$tool ; echo $toolrepo ; go get $toolrepo && go install $toolrepo ; done

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

CMD (flask run > /dev/null 2>&1) & (tini -s -- /usr/bin/python3 poseidon/main.py)
