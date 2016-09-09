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
    libhdf5-dev \
    python-tables \
    tcpdump && \
    easy_install pip

# install module dependencies
ADD requirements.txt requirements.txt
RUN pip install pip --upgrade
RUN pip install -r requirements.txt

# install blocks
RUN pip install git+https://github.com/PyTables/PyTables.git@develop#egg=tables
RUN pip install git+git://github.com/mila-udem/blocks.git@stable \
  -r https://raw.githubusercontent.com/mila-udem/blocks/stable/requirements.txt
RUN pip install numpy --upgrade

# test capture -- REMOVE FOR PRODUCTION
ADD testpcap.cap testpcap.cap

ADD train_deep_classifier.py train_deep_classifier.py
CMD ["python", "train_deep_classifier.py"]
