# ADR-0006: Docker Compose is the runtime, instead of Kubernetes

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT35, RT36, RT37 (applied through the container baseline)

## Context

The reference platform ran on a local Kubernetes cluster (kind + Helm charts + bash scripts).
That gives realism, but every change then involves charts, hooks, jobs and port forwards, which
is a lot of machinery for a two-person, local, teaching repository.

## Decision

The platform runs with **Docker Compose** (`compose.yaml` at the root, project name `orion`).
Each service follows the hardening baseline of [deployment.md](../deployment.md#rules-for-every-future-service):
pinned official images, multi-stage builds, non-root users, read-only filesystems, dropped
capabilities, loopback-only ports, Compose secrets, healthchecks and profiles.

## Alternatives considered

| Option | Why it lost |
|---|---|
| kind + Helm (as the reference) | heavy for the goal; slows every iteration; more to teach before anything useful |
| Plain `docker run` scripts | no declarative model of services, networks, volumes and dependencies |
| No containers (everything on the host) | environments drift; nothing to prove the deployment |

## Consequences

- + One file describes the runtime; `docker compose up` starts it; simple to read and teach.
- − No orchestration features (scaling, rolling updates, operators). RT30 says the prototype does
  not prove industrial capacity anyway; a move to Kubernetes would be its own ADR.
