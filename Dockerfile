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

ADD . /poseidonRest
WORKDIR /poseidonRest
RUN pip install -r poseidonRest/requirements.txt && rm -rf /root/.cache/pip/*

# install dependencies of plugins for tests
RUN for file in $(find plugins/* -name "requirements.txt"); \
    do \
        pip install -r $file; \
    done

# build documentation
#RUN ln -s /poseidon/plugins /poseidon/poseidon/plugins
RUN sphinx-apidoc -o docs poseidonRest -F && cd docs && make html && make man

ENV PYTHONUNBUFFERED 0
EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000"]
CMD ["poseidonRest.poseidonRest:api"]

# run linter
#RUN pylint --disable=all --enable=classes --disable=W poseidonRest

# run tests
RUN py.test -v --cov=poseidonRest --cov=plugins --cov-report term-missing
