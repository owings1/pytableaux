FROM alpine:latest

WORKDIR /app
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin

RUN addgroup -S appgroup && adduser -S appuser -G appgroup -h /app

# Required packages
RUN apk add --no-cache --update python3 curl py3-pip python3-dev build-base 

USER appuser
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir \
    future jinja2 cherrypy pytest coverage prometheus_client Sphinx

COPY --chown=appuser:appgroup . .

# Generate documentation
RUN cd doc && make clean html

HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080"]

CMD ["python3", "src/web.py"]