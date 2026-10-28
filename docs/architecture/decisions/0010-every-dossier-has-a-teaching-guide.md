# ADR-0010: Every dossier has a teaching guide, stored inside it and approved at G6

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision (mentoring goal)

## Context

The repository is used to mentor. Every feature must come with a detailed, didactic document that
explains every decision, from architecture changes to classes and abstractions, with many
diagrams. The question is where that document lives so that it is always written, always current
and easy to read as a course.

## Decision

- The guide is **`specs/<id>-<slug>/teaching-guide.md`**, created from a fixed fourteen-section
  template by `sdd new`.
- It is an artifact of **gate G6** together with `validation.md`: the merge cannot be approved
  until every section is present and no `TODO(sdd)` remains, and editing it after approval makes
  G6 stale.
- The documentation site assembles the guides into a **curriculum** (the
  [learning path](../../learn/README.md)), next to reusable primers on the concepts (SDD, clean
  architecture, SOLID, patterns, ADRs, EARS) and a glossary.

## Alternatives considered

| Option | Why it lost |
|---|---|
| A separate `docs/learn/chapters/` folder | away from the change it explains, so it is written late or not at all; not part of the gate |
| ADRs only | ADRs record decisions, not the walkthrough of code, patterns and runtime |
| Docstrings only | explain one unit at a time, never the whole picture |
| A wiki outside the repository | not versioned with the code, not reviewable, not checkable |

## Consequences

- + The guide is reviewed and approved with the change; it cannot lag.
- + The mentee reads one place per feature, in the order the features were built.
- − It is real work for every dossier. The teacher role and the `write-teaching-guide` skill make
  agents carry most of it; we judge its quality at G6.
