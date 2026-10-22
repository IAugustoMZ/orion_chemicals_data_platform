# ADR-0011: The requirements are transcribed into a machine-readable YAML catalogue

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT01-RT42 (all of them are its content)

## Context

The requirements arrive as a PDF. Agents can read it, but the harness also needs to *check*
references (gate G0), pre-fill PRDs with the cited requirements and their verification method,
and compute coverage. A PDF cannot be validated against.

## Decision

`docs/requirements/rt-catalog.yaml` transcribes the 42 requirements with id, category, phase
(P/A), priority, source RQs, an English statement and verification, and the original Portuguese
text. The PDF stays next to it and **wins on any disagreement**; corrections happen in the same
change as the discovery.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Read the PDF each time (text extraction) | layout breaks the text (columns, page breaks); no stable ids or fields |
| A Markdown table | readable, but parsing tables is brittle and multi-line cells are awkward |
| A database | overkill for 42 rows that change rarely |

## Consequences

- + G0 can reject an unknown RT; `sdd rt` prints requirements; the traceability matrix is
  generated.
- − The transcription must be kept faithful; a test asserts there are exactly 42 entries.
- How work that serves none of these requirements is handled:
  [ADR-0014](0014-work-outside-the-requirements-catalogue.md).
