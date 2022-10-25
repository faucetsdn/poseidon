FROM python:3.11-slim
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app
ENV PYTHONUNBUFFERED 1

CMD python3 worker.py
