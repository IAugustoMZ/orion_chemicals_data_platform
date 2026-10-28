# ADR-0001: We practise spec-driven development with our own lightweight harness

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT42 (automated validation before publication), supports all

## Context

The repository will be built largely by AI coding agents and is used to mentor. It must follow a
target operating model with seven phases, human approval gates and two planes (governed context,
AI control). Several SDD frameworks exist (GitHub Spec Kit, OpenSpec, BMAD-METHOD, Kiro; see the
[research](../../research/sdd-landscape.md)). None of them enforces human approval gates, none
models "we" as the only approvers, none ties work to a fixed requirement catalogue, and none asks
for a didactic record per change.

## Decision

We build our own lightweight harness: Markdown guides (constitution, lifecycle, gates, standards),
templates per phase, Agent Skills and roles, and a small Python tool `sdd` that evaluates gates,
records approvals, runs the quality suite, guards commits and regenerates derived documents. We
borrow the best ideas of the existing frameworks instead of adopting one of them wholesale.

## Alternatives considered

| Option | Fits the 7 phases + gates | Enforces approvals | Tool-agnostic | Ceremony | Verdict |
|---|---|---|---|---|---|
| Adopt Spec Kit as is | partly (no phases 3, 6, 7 as gates) | no | yes | low | lost: we would add the gates on top anyway and fight its folder layout |
| Spec Kit + our gates on top | yes, with glue | yes | yes | medium | lost: two sources of truth for the workflow; upgrades of Spec Kit could break the glue |
| BMAD-METHOD | partly | no | partly | high | lost: too heavy for two people; slow |
| Kiro | partly | no | no (its own IDE) | low | lost: ties us to one editor |
| **Own lightweight harness** | yes, by design | yes (TTY + digests) | yes | low | **chosen** |

## Consequences

- + The workflow is exactly the operating model, and every rule is visible and testable.
- + The harness is itself a teaching subject (dossier 000 explains its code).
- − We maintain the tool ourselves (about 1,600 statements of Python, 4,500 lines with docstrings, and 100+ tests).
- − No community templates or updates; we revisit this ADR if Spec Kit (or another framework)
  gains enforced gates and a pluggable lifecycle.
