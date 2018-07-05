FROM python:3.6.6-alpine3.7
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

RUN apk add --update \
    curl \
    gcc \
    git \
    linux-headers \
    musl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

RUN pip3 install --upgrade pip

# healthcheck
COPY healthcheck /healthcheck
RUN pip3 install -r /healthcheck/requirements.txt
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD (flask run > /dev/null 2>&1) & (gunicorn -b :8000 -k gevent -w 4 --reload app.app)
