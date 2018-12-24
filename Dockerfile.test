FROM redis:latest
FROM poseidon:latest
RUN apk upgrade --no-cache && \
    apk add --no-cache \
    build-base \
    python3-dev \
    yaml-dev
RUN pip3 install -r test-requirements.txt
RUN pip3 install -r api/requirements.txt
CMD py.test -v -vv --cov-report term-missing --cov=. -c .coveragerc
