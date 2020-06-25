FROM golang:stretch

ENV GO111MODULE="on"
RUN go get github.com/square/certstrap

COPY gen_faucetconfrpc_keys.sh /
WORKDIR /

ENTRYPOINT ["/gen_faucetconfrpc_keys.sh"]
