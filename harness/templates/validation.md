# Validation · {{id}} · {{title}}

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

TODO(sdd): The result of the last `poetry run sdd verify {{id}}`: commit, date, each check and
its verdict. G5 must be *passed* (not stale) when we approve G6.

## Code review

TODO(sdd): Findings of the code review (correctness, readability, tests, docstrings) and how
each was resolved. Use the checklist in [quality.md](../../harness/quality.md#3-code-review-checklist).

## Architecture review

TODO(sdd): Does the diff match the spec's architecture impact and the plan's file list? Layer
rules kept? ADRs written? Diagrams updated with logos?

## Security review

TODO(sdd): The STRIDE rows of the spec, each verified or explained; secrets, permissions,
inputs, dependencies ([security.md](../../harness/security.md)).

## Functional validation

TODO(sdd): For each SPEC behaviour and RT, how it was validated (test name, manual check,
measurement) and the result. Exploratory findings go here too.

| Behaviour or RT | How validated | Result |
|---|---|---|
| | | |

## Documentation upkeep

TODO(sdd): Tick what was updated, per [architecture-upkeep.md](../../harness/architecture-upkeep.md).

- [ ] ADRs created or superseded
- [ ] Architecture pages and diagrams (with official logos)
- [ ] Root README (and `poetry run sdd sync` run)
- [ ] Component READMEs and CONTRIBUTING
- [ ] Teaching guide complete

## Build log

TODO(sdd): Short log of the build loop: iterations, failed verifications and what fixed them,
escalations to us and our answers. Honest history, not a success story.

## Review notes (optional)

_Nothing needed to approve. Add a line here (or use `--note` when approving) only for a
condition on the merge or a decision worth remembering._
