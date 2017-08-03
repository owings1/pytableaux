FROM alpine:latest

MAINTAINER Doug Owings <doug@dougowings.net>

WORKDIR /mnt/app
EXPOSE 8080

# Required packages
RUN apk add --no-cache --update python curl py-pip && pip install --no-cache-dir jinja2 cherrypy

COPY . .

# Generate documentation
RUN apk add --no-cache --update python-dev build-base && pip install --no-cache-dir Sphinx && \
    cd doc && make clean html && \
    pip uninstall -y Sphinx && apk del python-dev build-base

# Tell the web server to listen on all interfaces
ENV PY_HOST=0.0.0.0

HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080"]

CMD ["python", "src/web.py"]