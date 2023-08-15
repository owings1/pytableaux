# syntax=docker/dockerfile:1
FROM docker.io/python:3.11.4-alpine as base

WORKDIR /app

RUN pip -qqq --no-cache-dir --no-input install pipenv

COPY ./Pipfile* ./
RUN pipenv install --quiet --deploy --system --extra-pip-args "-qqq --no-cache-dir --no-input"

FROM base as withweb
RUN pipenv install --quiet --deploy --system --extra-pip-args "-qqq --no-cache-dir --no-input"\
        --categories="web-packages"

FROM withweb as builder
RUN apk add --quiet --no-cache g++ make &&\
    pipenv install --quiet --deploy --system --extra-pip-args "-qqq --no-cache-dir --no-input"\
        --categories="doc-packages dev-packages" &&\
    apk del --quiet g++
COPY . .

FROM builder as doc
RUN python -m doc clean html BUILDDIR=/build

FROM doc as test
RUN python -m test &&\
    python -m doc doctest BUILDDIR=/build

FROM withweb

EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PT_DOC_DIR=/srv/doc
ENV PT_TEST_DIR=/srv/test

COPY --from=builder /app ./
COPY --from=doc /build/html ${PT_DOC_DIR}
COPY --from=test /app/htmlcov ${PT_TEST_DIR}

USER nobody

HEALTHCHECK CMD ["python", "-c", "from urllib import request;request.urlopen('http://localhost:8080/health')"]

CMD python -m pytableaux.web
