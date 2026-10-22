# ADR-0009: English is the only language of the repository

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision

## Context

The requirements and the operating model were written in Portuguese; the mentoring could use
either language. Mixing languages across code, harness and documents makes search, review and
agent instructions inconsistent.

## Decision

Everything we write is in English: code, comments, docstrings, harness, dossiers, ADRs, teaching
guides, commit messages. Source documents keep their original language and get an English
transcription next to them (the requirement catalogue keeps the Portuguese text in an `original`
field, ADR-0011).

## Alternatives considered

| Option | Why it lost |
|---|---|
| Portuguese for documents, English for code | two vocabularies for the same concepts; agents switch languages mid-artifact |
| Portuguese everywhere | identifiers and tool output are English anyway |

## Consequences

- + One vocabulary; the glossary is the single place for domain terms.
- − The original Portuguese wording must be checked when a translation is in doubt; the PDF wins.
