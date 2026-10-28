---
name: commit-review
description: Use before every commit and before asking for G6 to review the whole branch against the documentation upkeep matrix - ADRs, architecture pages, diagrams with logos, READMEs, teaching guide - and fix what lags.
---

# Commit review: documentation never lags the code

Rule and matrix: [harness/architecture-upkeep.md](../../../harness/architecture-upkeep.md).

## Steps

1. List what the branch changed:

   ```bash
   git diff --stat main...HEAD
   git status --short
   ```

2. Map each changed path to the upkeep matrix and open every document it names.
3. Compare against the code, not memory: module map vs `git ls-files tools src`, deployment page
   vs `compose.yaml`, ADR index vs the decisions folder, README quick start vs real commands.
4. Update what lags, in the same commit; add ADRs for decisions taken; update the teaching
   guide's code tour.
5. `poetry run sdd sync` then `poetry run sdd check`; both clean.
6. If nothing needed changing, say so in the commit message ("architecture and docs unchanged").

## Done when

Every document named by the matrix describes the branch as it is.
