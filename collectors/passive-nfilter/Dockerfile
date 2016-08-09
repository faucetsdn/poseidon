FROM alpine:3.4
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    python \
    py-pip \
    && rm -rf /var/cache/apk/*

ADD . /nfilter
RUN pip install -r requirements.txt
RUN pip install -r /nfilter/requirements.txt
WORKDIR /nfilter/nfilter

EXPOSE 8080

ENTRYPOINT ["python", "nfilter.py"]
CMD [""]
