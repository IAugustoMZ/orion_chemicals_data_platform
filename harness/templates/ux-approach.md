# Approach · {{id}} · {{title}}

> **Phase 3 · Structure**, closed by **G3 · Approach approved** (both of us approve).
> In a data platform the "user experience" is often an API, a command line, a dataset or a
> dashboard: *how a person or a system meets what we build*. How to fill this file:
> [lifecycle, phase 3](../../harness/lifecycle.md#phase-3-structure).

## Is a prototype needed?

TODO(sdd): Decide and justify. A prototype is needed when we are unsure *how* people will use
the result (a new screen, a new query interface). It is not needed when the interface follows an
existing contract or the work has no user-facing surface. "No, because ..." is a valid answer
and closes most of this file.

## Interface approach

TODO(sdd): Who interacts with the result, through which interface (HTTP API, CLI, dataset,
dashboard, file), and the main interactions. A Mermaid `journey` or `sequenceDiagram` from the
user's point of view is the clearest way to show it.

## Prototype (optional)

Where the prototype lives (folder, branch, link to a design) and what it mocks. Delete this
section when no prototype is needed.

## How we validate the approach

TODO(sdd): How we will know the approach works for its users before building it fully:
walk-through between us, a usability check with a scenario from the PRD, or "not applicable"
with the reason.
