# Backlog · {{id}} · {{title}}

> **Phase 2 · Plan**, closed by **G2 · Backlog approved** (both of us approve).
> The backlog lives in the repository as Markdown (ADR-0012); this file is its part for this
> dossier. How to fill it: [lifecycle, phase 2](../../harness/lifecycle.md#phase-2-plan).

## Epics

TODO(sdd): One to three epics: large outcomes that group features. One line each, with the PRD
goal they serve.

## Features

TODO(sdd): The features of each epic, one line each: what a user can do when it is delivered.

## Work items

TODO(sdd): One card per product backlog item (PBI). Acceptance criteria use EARS notation
(see [writing acceptance criteria](../../docs/learn/primers/acceptance-criteria.md)); every PBI
names the RTs it contributes to. Keep items small enough to build and review in one sitting.

### PBI-{{id}}-01 · Title

- **Feature:** TODO(sdd)
- **Serves:** RT..
- **Size:** S | M | L
- **Acceptance criteria (EARS):**
  - AC1: When `trigger`, the `system` shall `response`.
  - AC2: If `unwanted condition`, then the `system` shall `response`.

## Order and dependencies

TODO(sdd): In which order the items are built and why (risk first, dependencies, value). A
Mermaid `flowchart LR` of the dependencies helps when there are more than three items.

## Definition of done

Every item is done only when: its acceptance criteria are verified by tests, G5 passes, the
documentation upkeep in [architecture-upkeep.md](../../harness/architecture-upkeep.md) is done,
and the teaching guide explains it.

TODO(sdd): Add anything specific to this dossier, or write "nothing beyond the standard".
