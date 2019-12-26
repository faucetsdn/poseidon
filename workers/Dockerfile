FROM alpine:3.10
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck

RUN apk add --update \
    curl \
    gcc \
    linux-headers \
    musl-dev \
    python3 \
    python3-dev \
    && pip3 install --no-cache-dir --upgrade pip==19.1.1 \
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
ENV PYTHONUNBUFFERED 1

CMD (flask run > /dev/null 2>&1) & (python3 worker.py)
