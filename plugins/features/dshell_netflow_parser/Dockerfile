FROM ubuntu:16.04
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apt-get update && apt-get install -y git \
    python-crypto \
    python-dpkt \
    python-ipy \
    python-pip \
    python-pypcap \
    wget

RUN pip install pygeoip

RUN git clone https://github.com/USArmyResearchLab/Dshell.git

# install geo
WORKDIR /Dshell/share/GeoIP
RUN wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
RUN wget http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz
RUN wget http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz
RUN wget http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNumv6.dat.gz
RUN gunzip ./*.gz

WORKDIR /Dshell
RUN make

COPY . /dshell_netflow
WORKDIR /dshell_netflow
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "dshell_netflow_parser.py"]
CMD [""]
