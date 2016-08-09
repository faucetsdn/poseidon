FROM alpine:3.3
MAINTAINER Travis Lanham <tlanham@iqt.org>

RUN apk add --update \
    git \
    make \
    python \
    python-dev \
    py-pip \
    py-sphinx \
    tcpdump \
    && rm -rf /var/cache/apk/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD dns_verify.py dns_verify.py

ENTRYPOINT ["python", "dns_verify.py", "poseidon.tcpdump_parser.dns.#"]
CMD [""]
