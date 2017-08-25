FROM ubuntu:16.04
MAINTAINER Travis Lanham <tlanham@iqt.org>

# install packages
RUN apt-get update && \
    apt-get install -y \
    git \
    make \
    python \
    python-dev \
    build-essential \
    python-setuptools \
    tcpdump \
    python-pip \
    python-numpy

RUN easy_install pip
RUN pip install --upgrade pip==9.0.1

# install module dependencies
COPY requirements.txt requirements.txt
RUN pip install pip --upgrade
RUN pip install -r requirements.txt

COPY port_classifier.py port_classifier.py

# added entrypoint and cmd for vent injection of file name
ENTRYPOINT ["python", "port_classifier.py"]
CMD [""]
