---
name: sdd-plan
description: Phase 2 (Plan) of spec-driven development. Use to turn an approved PRD into backlog.md - epics, features and work items with EARS acceptance criteria and a risk-first order - until gate G2 is ready.
---

# Plan: build the backlog (phase 2 · gate G2)

Role: [backlog planner](../../../harness/roles/backlog-planner.md). Phase reference:
[lifecycle, phase 2](../../../harness/lifecycle.md#phase-2-plan).

## Steps

1. `poetry run sdd status <id>`: G1 must be passed.
2. Read `prd.md`, the cited RTs, and
   [acceptance criteria (EARS)](../../../docs/learn/primers/acceptance-criteria.md).
3. Fill `backlog.md`: epics (each tied to a PRD goal), features, and work items
   `PBI-<id>-NN` with feature, RTs served, size, and EARS acceptance criteria that a test can
   check.
4. Order the items risk-first and by dependency; draw a `flowchart LR` of dependencies when
   there are more than three items.
5. Check coverage: every cited RT appears in at least one item (say so if one does not).
6. `poetry run sdd check`, then hand over with the skill `sdd-review-gate`. Do not start
   `sdd-structure` until `sdd status` shows G2 passed. **Never run `sdd approve`.**

## Done when

Every item is small, traceable to a goal and to RTs, and has testable criteria.
