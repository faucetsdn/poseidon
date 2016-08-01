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
ADD pcap_stats.py pcap_stats.py 
ADD pcap_stats_utils.py pcap_stats_utils.py

ENTRYPOINT ["python", "pcap_stats.py", "poseidon.tcpdump_parser.#"]
CMD ["python", "pcap_stats.py", "poseidon.tcpdump_parser.#"]
