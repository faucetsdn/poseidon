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
ADD requirements.txt requirements.txt
RUN pip install pip --upgrade
RUN pip install -r requirements.txt

ADD eval_dev_classifier.py eval_dev_classifier.py

# added entrypoint and cmd for vent integration of file name
ENTRYPOINT ["python", "eval_dev_classifier.py"]
CMD [""]
