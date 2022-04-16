FROM python:3.10-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

COPY requirements.txt requirements.txt
COPY healthcheck /healthcheck

RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r /healthcheck/requirements.txt

# healthcheck
ENV FLASK_APP /healthcheck/hc.py
HEALTHCHECK --interval=15s --timeout=15s \
 CMD curl --silent --fail http://localhost:5000/healthcheck || exit 1

COPY . /app
WORKDIR /app
ENV PYTHONUNBUFFERED 1

CMD (flask run > /dev/null 2>&1) & (python3 worker.py)
