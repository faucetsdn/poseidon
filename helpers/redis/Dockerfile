FROM redis:5-alpine
LABEL maintainer="Charlie Lewis <clewis@iqt.org>"

HEALTHCHECK --interval=15s --timeout=15s \
 CMD redis-cli ping
CMD redis-server --appendonly yes
