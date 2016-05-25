FROM alpine:3.3
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    git \
    make \
    python \
    python-dev \
    py-pip \
    py-sphinx \
    && rm -rf /var/cache/apk/*

ADD . /poseidon
WORKDIR /poseidon
RUN pip install -r poseidon/requirements.txt

# build documentation
RUN sphinx-apidoc -o docs poseidon -F && cd docs && make html && make man

ENV PYTHONUNBUFFERED 0
EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000"]
CMD ["poseidon.poseidon:api"]

# run tests
RUN py.test -v --cov=poseidon --cov-report term-missing
