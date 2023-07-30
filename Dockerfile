# syntax=docker/dockerfile:1
FROM docker.io/python:3.11.4-alpine as base
WORKDIR /app
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin
RUN addgroup -S appgroup &&\
    adduser -S appuser -G appgroup -h /app &&\
    apk add --no-cache curl &&\
    pip -qqq --no-cache-dir --no-input install pipenv
COPY ./Pipfile* ./
RUN pipenv install --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input"

FROM base as doc
RUN apk add --no-cache g++ make &&\
    mkdir /build &&\
    pipenv install --dev --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input"
COPY . .
RUN cd doc &&\
    make clean html &&\
    mv _build/html /build &&\
    make clean

FROM base
COPY --from=doc --chown=root:root /app /app
COPY --from=doc /build/html /srv/doc
USER appuser
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PT_DOC_DIR=/srv/doc
HEALTHCHECK CMD ["curl", "--fail", "-I", "http://localhost:8080/health"]
CMD ["python", "-m", "pytableaux.web"]