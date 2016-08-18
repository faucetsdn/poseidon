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
ADD dev_classifier.py dev_classifier.py

ENTRYPOINT ["python", "dev_classifier.py", "poseidon.flowparser"]
CMD ["python", "dev_classifier.py", "poseidon.flowparser"]