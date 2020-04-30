FROM alpine:latest

WORKDIR /mnt/app
EXPOSE 8080

# Required packages
RUN apk add --no-cache --update python3 curl py3-pip && pip3 install --upgrade pip
RUN pip3 install --no-cache-dir future jinja2 cherrypy pytest coverage

# For documentation generation
RUN apk add --no-cache --update python3-dev build-base && pip3 install --no-cache-dir Sphinx 

COPY . .

# Generate documentation
RUN cd doc && make clean html
#    pip3 uninstall -y Sphinx && apk del python3-dev build-base

# Tell the web server to listen on all interfaces
ENV PY_HOST=0.0.0.0

HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080"]

CMD ["python3", "src/web.py"]