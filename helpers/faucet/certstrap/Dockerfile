FROM golang:1.15

ENV GO111MODULE="on"
RUN go get github.com/square/certstrap

WORKDIR /
COPY gen_faucetconfrpc_keys.sh gen_faucetconfrpc_keys.sh

ENTRYPOINT ["sh", "gen_faucetconfrpc_keys.sh"]
