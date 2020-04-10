FROM alpine:3.10
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="api"

COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck

RUN apk add --update \
    curl \
    gcc \
    linux-headers \
    musl-dev \
    python3 \
    python3-dev \
    && pip3 install --no-cache-dir --upgrade pip==20.0.2 \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir -r /healthcheck/requirements.txt \
    && apk del \
    gcc \
    linux-headers \
    musl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /app
WORKDIR /app

EXPOSE 8000

CMD (flask run > /dev/null 2>&1) & (gunicorn -b :8000 -k gevent -w 4 --reload app.app)
