FROM alpine:3.4
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    bash \
    tcpdump \
    && rm -rf /var/cache/apk/*

VOLUME /tmp
WORKDIR /tmp
COPY run.sh run.sh

CMD /tmp/run.sh
