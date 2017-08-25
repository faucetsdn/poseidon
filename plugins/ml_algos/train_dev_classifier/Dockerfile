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
    tcpdump && \
    easy_install pip

# install module dependencies
COPY requirements.txt requirements.txt
RUN pip install pip==9.0.1 --upgrade
RUN pip install -r requirements.txt

COPY train_dev_classifier.py train_dev_classifier.py

# added entrypoint and cmd for vent integration of file name
ENTRYPOINT ["python", "train_dev_classifier.py"]
CMD [""]
