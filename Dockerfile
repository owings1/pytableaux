# syntax=docker/dockerfile:1
FROM docker.io/python:3.11.4-alpine as base
WORKDIR /app
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/app/.local/bin
RUN pip -qqq --no-cache-dir --no-input install pipenv
COPY ./Pipfile* ./
RUN pipenv install --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input"
COPY . .

FROM base as doc
RUN apk add --quiet --no-cache g++ make &&\
    pipenv install --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input" \
        --categories="doc-packages" &&\
    apk del --quiet g++ &&\
    cd doc &&\
    make clean html BUILDDIR=/build

FROM doc as test
RUN pipenv install --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input" \
        --categories="dev-packages web-packages" &&\
    coverage run --source pytableaux -m pytest &&\
    coverage report -m &&\
    coverage html &&\
    cd doc &&\
    make clean doctest BUILDDIR=/build

FROM base
RUN pipenv install --quiet --deploy --system --extra-pip-args "--no-cache-dir --no-input" \
        --categories="web-packages" &&\
    rm -rf /app/test /app/doc /app/pytest.ini
COPY --from=doc /build/html /srv/doc
COPY --from=test /app/htmlcov /srv/test/coverage
COPY --from=test /build/doctest/output.txt /srv/test/doctest.txt
USER nobody
EXPOSE 8080 8181
ENV PT_HOST=0.0.0.0
ENV PT_DOC_DIR=/srv/doc
ENV PT_TEST_DIR=/srv/test
HEALTHCHECK CMD ["python", "-c", "from urllib import request;request.urlopen('http://localhost:8080/health')"]
CMD ["python", "-m", "pytableaux.web"]
