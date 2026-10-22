# ADR-0005: Poetry manages every Python environment, one project with dependency groups

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT24 (versions of code recorded), RT42

## Context

Several Python components will live in the repository (the `sdd` tool now; ingestion, catalog,
API later). Reproducible environments and a lock file are needed so that a check gives the same
answer on every machine, in pre-commit and in containers.

## Decision

Poetry (2.x) is the only environment and dependency manager. There is **one** `pyproject.toml`
at the root, with **dependency groups** per component (`dev` for the quality suite, `docs` for the
site, one group per platform component later). The virtual environment lives in `.venv/`
(`poetry.toml`). Containers install only their group, in a build stage (see
`docker/docs.Dockerfile`).

## Alternatives considered

| Option | Why it lost |
|---|---|
| One Poetry project per component | many lock files to keep in sync; shared tooling duplicated; the reference platform's single project worked well |
| uv | fast and capable, but the requirement for this repository is Poetry |
| pip + requirements files | no resolver-backed lock with groups; easy to drift |

## Consequences

- + One lock file; one `poetry install` for development; `poetry run` everywhere.
- − Groups must stay disciplined: a component's image must not pull another component's group.
