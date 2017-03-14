FROM ubuntu:16.04

MAINTAINER Doug Owings <doug@dougowings.net>

ENV TERM xterm-color

RUN apt-get update && apt-get -y install python python-pip dos2unix ntp wget zip unzip nano telnet

RUN pip install jinja2 cherrypy Sphinx

# the base directory of the repo. this mount must be provided at container creation time
ENV REPO_HOME /mnt/repo

RUN mkdir -p /usr/local/bin

COPY entrypoint.sh /usr/local/bin/

RUN dos2unix /usr/local/bin/entrypoint.sh && chmod 0755 /usr/local/bin/entrypoint.sh

EXPOSE 8080

WORKDIR $REPO_HOME

CMD ["/usr/local/bin/entrypoint.sh"]