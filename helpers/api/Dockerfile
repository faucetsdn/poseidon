FROM iqtlabs/poseidon:latest
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"
LABEL poseidon.namespace="api"

EXPOSE 8000

CMD (flask run > /dev/null 2>&1) & (poseidon-api)
