# syntax=docker/dockerfile:1
FROM python:3.11.2-alpine as base
WORKDIR /app
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin
RUN addgroup -S appgroup &&\
    adduser -S appuser -G appgroup -h /app &&\
    apk add --no-cache curl
USER appuser
COPY requirements.txt .
RUN pip -qqq --no-cache-dir install -r requirements.txt
USER root

FROM base as doc
RUN apk add --no-cache make && mkdir /build && chown appuser:appgroup /build
USER appuser
COPY requirements.doc.txt .
RUN pip -qqq --no-cache-dir install -r requirements.doc.txt
COPY --chown=appuser:appgroup . .
RUN cd doc && make clean html && mv _build/html /build && make clean

FROM base
USER appuser
COPY --from=doc /app /app
COPY --from=doc /build/html /srv/doc
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PT_DOC_DIR=/srv/doc
HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080/health"]
CMD ["python", "-m", "pytableaux.web"]