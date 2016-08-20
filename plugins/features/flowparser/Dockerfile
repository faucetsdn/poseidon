FROM golang:alpine
MAINTAINER Travis Lanham <tlanham@iqt.org>

RUN apk add --update \
    git \
    gcc \
    libc-dev \
    make \
    libpcap \
    libpcap-dev

ADD . src/flowparser

# install rabbitmq package
RUN go get github.com/streadway/amqp

# install and build flowtbag
RUN go get github.com/DanielArndt/flowtbag
WORKDIR /go/src/github.com/DanielArndt/flowtbag/
RUN go build

# copy flowtbag binary to flowparser
RUN cp flowtbag /go/src/flowparser/

# set workdir to flowparser
WORKDIR /go/src/flowparser

CMD ["go", "run", "flowparser.go", "testpcap.cap"]
