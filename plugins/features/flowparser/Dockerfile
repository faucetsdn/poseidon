FROM golang:1.7
MAINTAINER Travis Lanham <tlanham@iqt.org>

ADD . /flowparser
WORKDIR /flowparser

# install rabbitmq package
RUN go get github.com/streadway/amqp

RUN go build
