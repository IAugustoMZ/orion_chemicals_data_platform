# ADR-0026: A rationale is required for every dossier

- **Status:** Accepted
- **Date:** 2026-11-13
- **Dossier:** specs/002-harness-item-flow (card 05)
- **Requirements:** RT42; amends [ADR-0014](0014-work-outside-the-requirements-catalogue.md)

## Context

ADR-0014 asked for a rationale only from enablers and from features that cite no RT. A feature
that cites RTs could be created with no reason at all, so the "why" was missing exactly where it
is easiest to forget. The reason also reads best in `dossier.yaml`, next to the RTs.

## Decision

Every dossier states its rationale. `sdd new` requires `--rationale` (Typer rejects a missing
option with exit 2) and the use case rejects a blank one before writing anything, so any other
entry point is covered. G0 fails for an empty or whitespace rationale, whatever the kind, with
"a dossier must state its rationale in dossier.yaml". Existing dossiers already have one.

## Consequences

- **Good:** one rule, no per-kind exceptions; the reason is always on record.
- **Cost:** `sdd new` calls and test fixtures need a rationale.
- **Not covered:** the quality of the rationale; people judge that at G1.
- ADR-0014 keeps its other rules (outside the catalogue, list the RTs considered).
