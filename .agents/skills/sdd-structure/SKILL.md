---
name: sdd-structure
description: Phase 3 (Structure) of spec-driven development. Use to decide whether a prototype is needed and to describe the interface approach (API, CLI, dataset, dashboard) in ux-approach.md, until gate G3 is ready.
---

# Structure: choose the interface approach (phase 3 · gate G3)

Role: [UX designer](../../../harness/roles/ux-designer.md). Phase reference:
[lifecycle, phase 3](../../../harness/lifecycle.md#phase-3-structure).

## Steps

1. `poetry run sdd status <id>`: G2 must be passed.
2. Read `prd.md` (users, scenarios) and `backlog.md`; look at the existing interfaces of the
   platform for consistency.
3. In `ux-approach.md`, decide **whether a prototype is needed** and justify it. Most data work
   needs none; say why.
4. Describe the **interface approach**: who, through what, main interactions, as a Mermaid
   `journey` or `sequenceDiagram` from the user's side.
5. If a prototype is needed: build it in a clearly separated folder with a mocked back end
   (this is not governed production code; keep it out of `src/` and `tools/`), and describe it.
6. Say how we will validate the approach (walk-through of a PRD scenario, or not applicable).
7. `poetry run sdd check`, then hand over with the skill `sdd-review-gate`. Do not start
   `sdd-specify` until `sdd status` shows G3 passed. **Never run `sdd approve`.**

## Done when

We can judge from `ux-approach.md` alone whether people will succeed with the interface.
