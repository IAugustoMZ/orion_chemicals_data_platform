# Execution specification · {{id}} · {{title}}

> **Phase 4 · Specify**, closed by **G4 · Specification approved for execution** (both of us
> approve `spec.md`, `plan.md` and `tasks.md` together). After G4, code may change on branch
> `{{branch}}`. Any later edit of these three files makes G4 stale until we re-approve.
> How to fill this file: [lifecycle, phase 4](../../harness/lifecycle.md#phase-4-specify).

> **Tables first.** Wherever the content is a list of things with attributes (sources, behaviours,
> components, contracts, classes, patterns, ADRs, documents, exclusions), use a table, one row per
> thing, so we can scan, compare and review row by row. Prose is for the few sentences a table
> cannot hold; diagrams are for shape and flow. A table cell holds one fact: if it needs a
> paragraph, shorten it and link to where the detail lives.

## Context collected

TODO(sdd): What was read to write this spec, so a reviewer can check nothing was missed: the
RTs ({{requirements}}), the approved artifacts, the ADRs, the modules and documents of the
codebase, external references. One row per source.

| Source | Where | What it contributed |
|---|---|---|
| | | |

## Behaviour

TODO(sdd): The observable behaviour, as numbered EARS statements, one row each. Each one is
testable and names the RTs and the acceptance criteria it implements. This is the contract the
build must satisfy.

| ID | Behaviour (EARS) | RT | Backlog criteria |
|---|---|---|---|
| SPEC-{{id}}-B01 | When `trigger`, the `system` shall `response`. | RT.. | PBI-{{id}}-01 AC1 |

## Architecture impact

TODO(sdd): What changes in the architecture. Draw the affected part *before* and *after* as
Mermaid flowcharts with the official logo of every tool
([documentation standard](../../harness/documentation-standard.md#diagrams-and-official-logos)).
Then list every component added, changed or removed, and every new dependency, as tables.

| Component | Change (added, changed, removed) | Layer or place | Why |
|---|---|---|---|
| | | | |

| Dependency | Version or source | Group (runtime, dev, docs) | Why |
|---|---|---|---|
| | | | |

## Contracts and data

TODO(sdd): The interfaces other parts rely on: one row per API endpoint, file or table schema,
event or configuration, with a Mermaid `erDiagram` where the data has relations. Say what is
versioned and how compatibility is kept (RT15, RT32).

| Contract | Shape (fields, format, exit codes) | Producer | Consumers | Versioning |
|---|---|---|---|---|
| | | | | |

## Design

TODO(sdd): The internal design as tables, plus a Mermaid `classDiagram` for the structure: the
layers touched with each class and its single responsibility, the design patterns chosen and
why, and how the design respects SOLID and clean architecture
([principles](../../harness/principles.md)).

| Layer | Class or module | Responsibility (one reason to change) | Collaborators (ports) |
|---|---|---|---|
| | | | |

| Pattern | Where | Why this one (and the alternative that lost) |
|---|---|---|
| | | |

| SOLID principle | How the design respects it |
|---|---|
| | |

## Security and threat model

TODO(sdd): STRIDE, one row per threat that applies; "not applicable" needs a reason.

| Threat (STRIDE) | Where | Mitigation | Verified by |
|---|---|---|---|
| | | | |

## Validation plan

TODO(sdd): How each behaviour and each RT's "how we verify it" will be proven: unit,
integration or end-to-end test, a measurement, or a manual check by us. Every SPEC-B line
appears here at least once.

| Behaviour or RT | Test level | Test or evidence | Data needed |
|---|---|---|---|
| | | | |

## Architecture decisions

TODO(sdd): The ADRs this work creates or supersedes, one row each, with status *Proposed* until
G4 (then *Accepted*). Write "none" with a reason if the work fits existing decisions.

| ADR | Decision | Status | Refines or supersedes |
|---|---|---|---|
| `docs/architecture/decisions/NNNN-title.md` | | Proposed | |

## Documentation impact

TODO(sdd): Which documents change with this work, following the upkeep matrix in
[architecture-upkeep.md](../../harness/architecture-upkeep.md): architecture pages, diagrams,
READMEs, the root README, the teaching guide. One row per document.

| Document | Change | Upkeep rule |
|---|---|---|
| | | |

## Out of scope

TODO(sdd): What this specification deliberately leaves out, so the build does not drift. One row
per exclusion, with where it goes instead.

| Excluded | Why | Where it goes |
|---|---|---|
| | | |
