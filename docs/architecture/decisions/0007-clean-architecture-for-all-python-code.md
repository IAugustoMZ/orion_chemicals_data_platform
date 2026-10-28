# ADR-0007: All Python code follows clean architecture, enforced by import-linter

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT19 (same rules for every consumer), RT42

## Context

Agents write most of the code. Without a structure they can check, layers erode quickly: business
rules leak into routers, frameworks into the domain. The repository is also a teaching tool, so
the structure must be explicit and explainable.

## Decision

Every Python package has `domain`, `application` (use cases + ports as `typing.Protocol`),
`infrastructure` (adapters), `bootstrap` (composition root) and `interfaces`. Dependencies point
inwards only. The rules are **import-linter contracts** in `pyproject.toml`, checked in pre-commit
and in G5; the `sdd` tool is the first example (three contracts: layers; interfaces never reach
infrastructure directly; domain and application free of frameworks and I/O libraries).

## Alternatives considered

| Option | Why it lost |
|---|---|
| A flat package per component | fastest to start; impossible to keep frameworks out of rules as it grows |
| Layers as a convention only | erodes under agent-written code; a reviewer cannot catch every import |
| A framework-imposed structure (e.g. Django apps) | ties the domain to a framework |

## Consequences

- + The domain is testable in milliseconds with in-memory fakes; adapters are swappable.
- + Violations fail the commit, so the structure survives agents.
- − More files and indirection than a script needs; small tools outside the platform (like the
  agent hook, which must run without dependencies) are explicit, documented exceptions.
