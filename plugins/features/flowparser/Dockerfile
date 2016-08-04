FROM golang
MAINTAINER Travis Lanham <tlanham@iqt.org>

ADD . /go/src/flowparser
RUN go install /go/src/flowparser

ENTRYPOINT /go/bin/flowparser
