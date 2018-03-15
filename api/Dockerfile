FROM python:3-alpine3.6
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

RUN apk add --update \
    gcc \
    git \
    linux-headers \
    musl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["gunicorn"]
CMD ["-b", ":8000", "-k", "gevent", "-w", "4", "--reload", "app.app"]
