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

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY pcap_stats.py pcap_stats.py 
COPY pcap_stats_utils.py pcap_stats_utils.py

# entrypoint and cmd for vent injection of file name
ENTRYPOINT ["python", "pcap_stats.py"]
CMD [""]
