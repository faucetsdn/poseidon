FROM alpine:3.4
MAINTAINER Travis Lanham <tlanham@iqt.org>

RUN apk add --update python py-pip && rm -rf /var/cache/apk/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD dns_verify.py dns_verify.py

ENTRYPOINT ["python", "dns_verify.py"]
CMD [""]