FROM alpine:3.3
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    git \
    make \
    python \
    python-dev \
    py-pip \
    py-sphinx \
    tcpdump \
    && rm -rf /var/cache/apk/*

ADD . /poseidon
WORKDIR /poseidon
RUN pip install -r poseidon/requirements.txt && rm -rf /root/.cache/pip/*

# install dependencies of plugins for tests
RUN for file in $(find plugins/* -name "requirements.txt"); \
    do \
        pip install -r $file; \
    done

# build documentation
RUN ln -s /poseidon/plugins /poseidon/poseidon/plugins
RUN sphinx-apidoc -o docs poseidon -F --follow-links && cd docs && make html && make man

ENV PYTHONUNBUFFERED 0
EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000"]
CMD ["poseidon.poseidon:api"]

# run linter
#RUN pylint --disable=all --enable=classes --disable=W poseidon

# run tests
RUN py.test -v --cov=poseidon --cov=plugins --cov-report term-missing
