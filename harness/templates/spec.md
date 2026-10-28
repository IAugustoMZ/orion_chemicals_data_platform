# Execution specification · {{id}} · {{title}}

> **Phase 4 · Specify**, closed by **G4 · Specification approved for execution** (both of us
> approve `spec.md`, `plan.md` and `tasks.md` together). After G4, code may change on branch
> `{{branch}}`. Any later edit of these three files makes G4 stale until we re-approve.
> How to fill this file: [lifecycle, phase 4](../../harness/lifecycle.md#phase-4-specify).

## Context collected

TODO(sdd): What was read to write this spec, so a reviewer can check nothing was missed: the
RTs ({{requirements}}), the ADRs, the modules and documents of the codebase, external
references. One bullet per source with one line on what it contributed.

## Behaviour

TODO(sdd): The observable behaviour, as numbered EARS statements. Each one is testable and names
the RTs and acceptance criteria it implements. This is the contract the build must satisfy.

- **SPEC-{{id}}-B01:** When `trigger`, the `system` shall `response`. *(RT.., PBI-{{id}}-01 AC1)*

## Architecture impact

TODO(sdd): What changes in the architecture. Draw the affected part *before* and *after* as
Mermaid flowcharts with the official logo of every tool
([documentation standard](../../harness/documentation-standard.md#diagrams-and-official-logos)),
list the components added, changed or removed, and every new dependency.

## Contracts and data

TODO(sdd): The interfaces other parts rely on: API endpoints and payloads, file or table
schemas (Mermaid `erDiagram`), events, configuration. Say what is versioned and how
compatibility is kept (RT15, RT32).

## Design

TODO(sdd): The internal design: the layers touched, the classes and their responsibilities
(Mermaid `classDiagram`), the design patterns chosen and why, and how the design respects SOLID
and clean architecture ([principles](../../harness/principles.md)).

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

TODO(sdd): The ADRs this work creates or supersedes, each with status *Proposed* until G4 (then
*Accepted*). Link them: `docs/architecture/decisions/NNNN-title.md`. Write "none" with a reason
if the work fits existing decisions.

## Documentation impact

TODO(sdd): Which documents change with this work, following the upkeep matrix in
[architecture-upkeep.md](../../harness/architecture-upkeep.md): architecture pages, diagrams,
READMEs, the root README, the teaching guide.

## Out of scope

TODO(sdd): What this specification deliberately leaves out, so the build does not drift.
