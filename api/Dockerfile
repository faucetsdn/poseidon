FROM ubuntu:14.04.4
MAINTAINER clewis@iqt.org

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y git npm nodejs openjdk-7-jre
RUN ln -s /usr/bin/nodejs /usr/local/bin/node

RUN git clone https://github.com/swagger-api/swagger-ui.git
WORKDIR /swagger-ui
RUN git checkout tags/v2.1.4
RUN npm install
EXPOSE 8080
ADD index.html /swagger-ui/dist/index.html
ADD swagger-ui.js /swagger-ui/dist/swagger-ui.js
CMD ./node_modules/gulp/bin/gulp.js serve
