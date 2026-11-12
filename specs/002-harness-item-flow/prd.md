# PRD · 002 · Harness: item-by-item flow and CI

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/002-harness-item-flow/` · branch `spec/002-harness-item-flow` · kind **feature** · created 2026-11-12.
> Child of the umbrella dossier [001](../001-timeseries-source/prd.md); size rule: every spec is at most 50 lines.

## Requirements digest

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT42 | P | Changes to integrations and rules shall pass automated validation of contracts, exceptions and regression before publication. | Introduce an incompatibility, observe a controlled failure, then fix it. |
| RT38 | P | Changes to mappings, rules, permissions and manual reprocessing shall record actor, time, reason and before/after when applicable. | Make a change and reconstruct it from the audit log. |

**In plain words.** RT42 is served by a server-side pipeline that blocks a merge unless every
quality check passes. RT38 is served by a per-card approval that records member, time, digest and
git identity, so a card's approval can be reconstructed later. Related RTs left out: RT36 (the
pipeline holds no secret, it must not break); RT01 does not apply (no industrial system).

## Problem

Until now one approval covered a whole backlog and all code lived on one spec branch. For a
21-card dossier that makes reviews huge, hides progress, and freezes cards that change once
earlier ones exist. Local pre-commit is also skippable (`--no-verify`, another clone), and
commits are blocked today by a status-table bug. Dossiers also may start with an empty rationale.

## Goals and success metrics

| Goal | Metric | Baseline | Target | How we measure |
|---|---|---|---|---|
| Build a backlog one card at a time | cards built on their own branch, approved on their own digest, merged by a person | 0 | 100 % of cards of later dossiers | `sdd item status`; `progress.yaml` |
| No unchecked change reaches `main` | pull requests merged with a red check | possible | 0 | deliberate type error: red, merge blocked, fix, green |
| Dossiers always say why | dossiers with an empty rationale | 1 | 0 can be created | `sdd new` without rationale exits 2 |
| `sdd check` passes on a new dossier | broken links after `sdd new` | 2 | 0 | `sdd check` exits 0 |

## Users and scenarios

- **Mentor and mentee** approve one card, wait for the pull request, merge it, and the agent starts
  the next card from an updated `main`.
- **The agent** builds a card until each acceptance criterion has a passing marked test, opens a
  pull request and stops; it never merges.

## Scope

### In scope
- Cards 01 (status link), 22 (item flow), 23 (CI), 02 (rationale) of the 001 backlog.
- ADR-0023 (item flow) and ADR-0024 (CI, supersedes ADR-0004), already drafted.

### Out of scope
- Merging pull requests, and applying GitHub branch protection (a person does both).
- Deployment pipelines, self-hosted runners, notifications.

## Constraints and assumptions

- Local-only runtime; GitHub only stores the repository and runs the checks (decision, 2026-11-04).
- The agent guard (`tools/agent_hooks/`) is changed by us, not by an agent.
- Assumption: the repository is on GitHub and branch protection is available to us.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| The pipeline exists but branch protection is not applied | RT42 claimed, not true | checklist and a red-then-green proof by us (mentor) |
| `sdd item next` deletes a branch with unmerged work | lost work | safe delete only; it lists branches first (mentee) |
| Existing dossier 000 breaks under new G2/G5 rules | harness regression | dossiers without `progress.yaml` keep the old rules (mentee) |
