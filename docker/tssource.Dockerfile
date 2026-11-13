# syntax=docker/dockerfile:1
#
# The plant data generator `tssource` (dossier 003, ADR-0019), run by `docker compose up tssource`.
#
# Two stages, as in docs.Dockerfile: the builder installs Poetry and the `main` and `tssource` dependency
# group into a virtual environment; the final image copies only that environment and the package
# source, so no compiler, Poetry or pip cache ships. The base image is pinned by digest
# (python:3.12-slim at the time of writing); update the digest on purpose, never by drift.
#
# With no arguments the container idles so that it can be reported healthy; with arguments it
# runs the command: `docker compose run --rm tssource bench --format parquet`.

ARG PYTHON_IMAGE=python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

FROM ${PYTHON_IMAGE} AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.3.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
RUN pip install "poetry==${POETRY_VERSION}" && python -m venv /opt/venv
WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main,tssource --no-root --no-interaction --no-ansi
RUN printf '#!/opt/venv/bin/python\nfrom tssource.interfaces.cli.app import main\nmain()\n' \
      > /opt/venv/bin/tssource \
    && printf '#!/bin/sh\nif [ "$#" -eq 0 ]; then exec python -c "import signal; signal.pause()"; fi\nexec tssource "$@"\n' \
      > /opt/venv/bin/tssource-entry \
    && chmod 0755 /opt/venv/bin/tssource /opt/venv/bin/tssource-entry

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    TSSOURCE_OUT=/data/ts_source
COPY --from=builder /opt/venv /opt/venv
COPY src /app/src
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin tssource
USER 10001
WORKDIR /app
ENTRYPOINT ["tssource-entry"]
