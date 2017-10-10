FROM continuumio/anaconda3
MAINTAINER dgrossman@iqt.org

COPY . /poseidonWork
WORKDIR /poseidonWork
RUN ln -s /poseidonWork /tmp/poseidonWork 
ENV PYTHONPATH /poseidonWork/poseidon:$PYTHONPATH

# install dependencies of poseidon modules for poseidon
RUN find . -name requirements.txt -type f -exec pip install -r {} \;

ENV PYTHONUNBUFFERED 0
ENV SYS_LOG_HOST NOT_CONFIGURED
ENV SYS_LOG_PORT 514

# Add Tini
ENV TINI_VERSION v0.16.1
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

# run tests
RUN py.test -v --cov=./poseidon -c .coveragerc

CMD ["python","/poseidonWork/poseidon/poseidonMonitor/poseidonMonitor.py"]
