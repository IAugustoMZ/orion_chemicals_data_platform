# PRD · {{id}} · {{title}}

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/{{id}}-{{slug}}/` · branch `{{branch}}` · kind **{{kind}}** · created {{date}}.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

{{requirements_table}}

TODO(sdd): In two or three sentences, say what these requirements mean for this work in plain
words, and name any related RT that is deliberately left out (and why). If no RT is cited (work
outside the catalogue), list the RTs that were considered, why none applies, and the RTs this
work must still not break (for example RT01 read-only access, RT36 no credentials).

## Problem

TODO(sdd): The need, told as a story: who at Orion Chemicals suffers today, what happens, and
what it costs (time, risk, money). No solution yet.

## Goals and success metrics

TODO(sdd): Two to four measurable outcomes. Use the table; "how we measure" must be something we
can actually run or observe.

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| | | | | |

## Users and scenarios

TODO(sdd): Who uses the result (operator, reliability engineer, data analyst, data scientist,
another system) and the two or three scenarios that matter most, one paragraph each.

## Scope

### In scope

TODO(sdd): Bullet list of what this work delivers.

### Out of scope

TODO(sdd): Bullet list of what it deliberately does not deliver (as important as the above).

## Constraints and assumptions

TODO(sdd): What limits the solution: read-only access to industrial systems (RT01), data
classification, volumes, the local-only runtime (Docker Compose), time available. Mark each
assumption so we can check it later.

## Risks and open questions

TODO(sdd): The risks (impact, likelihood, mitigation) and the questions still open, each with
who of us answers it.

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| | | |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
