FROM alpine:3.4
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    python \
    py-pip \
    tcpdump \
    && rm -rf /var/cache/apk/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD tcpdump_hex_parser.py tcpdump_hex_parser.py

ENTRYPOINT ["python", "tcpdump_hex_parser.py"]
CMD [""]
