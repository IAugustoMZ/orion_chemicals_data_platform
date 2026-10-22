# syntax=docker/dockerfile:1
#
# The documentation site (MkDocs + Material), served by `docker compose up docs` (ADR-0008).
#
# Two stages: the builder installs Poetry and the `docs` dependency group into a virtual
# environment; the final image copies only that environment, so Poetry and pip's caches never
# ship. The repository itself is mounted read-only at run time (compose.yaml), so the image holds
# no project content and editing a page needs no rebuild.

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.3.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
RUN pip install "poetry==${POETRY_VERSION}" && python -m venv /opt/venv
WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN poetry install --only docs --no-root --no-interaction --no-ansi

FROM python:${PYTHON_VERSION}-slim AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /opt/venv /opt/venv
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin docs
USER 10001
WORKDIR /workspace
EXPOSE 8000
CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8000", "--livereload"]
