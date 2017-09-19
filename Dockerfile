FROM ubuntu:16.04
Maintainer dgrossman@iqt.org

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

RUN pip install pip==9.0.1 --upgrade

COPY . /poseidonWork
WORKDIR /poseidonWork
ENV PYTHONPATH /poseidonWork/poseidon:$PYTHONPATH

# install dependencies of poseidon modules for poseidon
RUN find . -name requirements.txt -type f -exec pip install -r {} \;

ENV PYTHONUNBUFFERED 0

# Add Tini
ENV TINI_VERSION v0.16.1
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

# run tests
RUN py.test -v \
--cov=poseidon/poseidonMonitor \
--cov-report term-missing --cov-config .coveragerc

CMD ["python","/poseidonWork/poseidon/poseidonMonitor/poseidonMonitor.py"]
