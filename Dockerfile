FROM python:3.11.2-alpine

WORKDIR /app
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin

RUN addgroup -S appgroup && adduser -S appuser -G appgroup -h /app

# Required packages
RUN apk add --no-cache --update bash python3 curl py3-pip python3-dev build-base 

USER appuser
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY --chown=appuser:appgroup . .

# Generate documentation
RUN cd doc && make clean html

HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080"]

CMD ["bash", "scripts/start.sh"]