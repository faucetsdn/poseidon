FROM alpine:3.4
MAINTAINER Travis Lanham <tlanham@iqt.org>

RUN apk add -- update \
    python \
    py-pip \
    && rm -rf /var/cache/apk/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD pcap_stats.py pcap_stats.py

ENTRYPOINT ["python", "pcap_stats.py"]
CMD [""]