FROM alpine:3.4
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    python \
    tcpdump \
    && rm -rf /var/cache/apk/*

COPY tcpdump_hex_parser.py tcpdump_hex_parser.py

ENTRYPOINT ["python", "tcpdump_hex_parser.py"]
CMD [""]
