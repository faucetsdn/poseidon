FROM ubuntu:16.04
MAINTAINER Travis Lanham <tlanham@iqt.org>

# install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    make \
    python \
    python-dev \
    build-essential \
    python-setuptools \
    tcpdump && \
    easy_install pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install module dependencies
COPY requirements.txt requirements.txt

RUN pip install pip==9.0.1 --upgrade
RUN pip install -r requirements.txt

COPY eval_dev_classifier.py eval_dev_classifier.py

# added entrypoint and cmd for vent integration of file name
ENTRYPOINT ["python", "eval_dev_classifier.py"]
CMD [""]
