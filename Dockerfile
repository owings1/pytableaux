FROM python:3.11.2-alpine

WORKDIR /app
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin

RUN addgroup -S appgroup &&\
    adduser -S appuser -G appgroup -h /app &&\
    apk add --no-cache curl make

USER appuser
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appgroup . .

# Generate documentation
RUN cd doc && make clean html

HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080"]

CMD ["scripts/start.sh"]