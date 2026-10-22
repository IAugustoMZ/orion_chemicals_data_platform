---
name: sdd-discover
description: Phase 1 (Discover) of spec-driven development. Use to draft or revise a dossier's prd.md from our need and the cited requirements, until gate G1 (PRD validated) is ready for our approval.
---

# Discover: draft the PRD (phase 1 · gate G1)

Role: [product analyst](../../../harness/roles/product-analyst.md). Phase reference:
[lifecycle, phase 1](../../../harness/lifecycle.md#phase-1-discover).

## Steps

1. `poetry run sdd status <id>`: G0 must be passed and G1 not yet passed.
2. Read the cited RTs (`poetry run sdd rt <ids>`) and everything we provided about the need.
3. Fill `specs/<id>-<slug>/prd.md` section by section, replacing every `TODO(sdd)`:
   requirements digest (plain words, related RTs left out; outside the catalogue: the RTs
   considered and why none applies), problem as a story, two to four
   measurable goals (baseline, target, how measured), users and scenarios, scope in/out,
   constraints and assumptions, risks and open questions (with an owner: mentor or mentee).
4. Do not invent business facts: unknowns go to "Risks and open questions" and to your message.
5. Leave "Review notes (optional)" empty: approving needs no prose from us.
6. Run `poetry run sdd check` and fix any finding about this dossier.
7. Hand over with the skill `sdd-review-gate`: we review in the chat, then approve at our
   terminals. Do not start `sdd-plan` until `sdd status` shows G1 passed.
   **Never run `sdd approve`.**

## Done when

`prd.md` has no `TODO(sdd)` and our questions are listed.
