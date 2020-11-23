FROM python:3.8-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="api"

COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck

RUN apt-get update && apt-get install -y --no-install-recommends curl gcc build-essential libssl-dev libffi-dev python-dev && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir -r /healthcheck/requirements.txt && \
    apt-get purge -y gcc build-essential libssl-dev libffi-dev python-dev && apt -y autoremove --purge && rm -rf /var/cache/* /root/.cache/*

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /app
WORKDIR /app

EXPOSE 8000

CMD (flask run > /dev/null 2>&1) & (gunicorn -b :8000 -k gevent -w 4 --reload app.app)
