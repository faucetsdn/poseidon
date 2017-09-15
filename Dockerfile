FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    make \
    python \
    python-dev \
    python-pip \
    python-setuptools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /poseidonWork
WORKDIR /poseidonWork
ENV PYTHONPATH /poseidonWork/poseidon:$PYTHONPATH
RUN pip install pip==9.0.1 --upgrade

# install dependencies of poseidon modules for poseidon
RUN for file in $(find poseidon/* -name "requirements.txt"); \
    do \
        pip install -r $file; \
    done

ENV PYTHONUNBUFFERED 0

# run linter
#RUN pylint --disable=all --enable=classes --disable=W poseidonMonitor

# run tests
RUN py.test -v \
--cov=poseidon/poseidonMonitor \
--cov-report term-missing --cov-config .coveragerc

CMD ["python","/poseidonWork/poseidon/poseidonMonitor/poseidonMonitor.py"]
