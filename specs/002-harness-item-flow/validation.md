# Validation · 002 · Harness: item-by-item flow and CI

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

`poetry run sdd verify 002` passed on 2026-11-13 at commit `efa83c3` (working tree with the
documentation edits of branch `docs/002-g5-verified`): format, lint, types, architecture, tests,
security, secrets, dependencies, harness and docs-site, all PASS. All five cards (01-05) are
merged; the card proofs ran earlier with `sdd item verify 002 <nn>`.

## Code review

Independent `reviewer` subagent, 2026-11-13, against the spec, plan, backlog and
[quality.md](../../harness/quality.md#3-code-review-checklist). No blocking finding. All 24
acceptance criteria of cards 01-05 have a test marked `@pytest.mark.ac`. Docstrings state why and
contract. Findings and resolution:

| # | Finding | Resolution |
|---|---|---|
| 1 | Action SHAs in `ci.yml` unverified | Fixed: `git ls-remote` shows checkout v4.2.2 = `11bd7190…` and setup-python v5.3.0 = `0b93645e…`; caveats removed |
| 2 | Card 05 text says ADR-0025; the ADR is 0026 | Accepted as a known gap: editing an approved, merged card would void its approvals |
| 3 | Merge is not blocked (no branch protection) | Accepted limitation, see Security review |
| 5 | `ensure_allowed` is a deny-list matching only the first argument (`git -c x=y push` passes) | Accepted: all call sites are internal and fixed; an allow-list is a later hardening |
| 7 | `pipx install poetry==2.3.4` not hash-pinned; unquoted `$(git ls-files)` | Accepted: version-pinned; no path has spaces |
| 8 | `deployment.md` describes CI in prose, no diagram | Accepted nit; the teaching guide has the flow diagram with logos |

## Architecture review

The diff matches the spec's architecture impact and the plan's file list: domain
(`item_progress`, `card_digest`), application (use cases, ports `ProgressRepository`,
`GitRepository`, `AcStatusReader`), infrastructure (YAML, git CLI, pytest reader), interfaces
(`item` group) and `.github/workflows/ci.yml`. Layer rules are enforced by import-linter (PASS in
G5). ADR-0023, ADR-0024 and ADR-0026 are Accepted, ADR-0004 is Superseded, and the ADR index is
current.

## Security review

| STRIDE row | Verdict |
|---|---|
| Tampering: edit `progress.yaml`, bypass hooks, force push | Verified by the digest, git-adapter and CI tests (B02, B04, B05). The `quality` job reports on every PR, but **branch protection is not applied** (free private repository), so the block is our discipline: we merge only on a green `quality`. Documented in [ci-protection.md](../../harness/ci-protection.md) and ADR-0024 |
| Elevation: token or unpinned action | Verified: `contents: read`, `persist-credentials: false`, no secret, pins checked against tags, trigger is `pull_request`, branch name passed through `env:` |

Secrets: none found. Dependencies: `pip-audit` PASS in G5.

## Functional validation

| Behaviour or RT | How validated | Result |
|---|---|---|
| B01 (RT42) teaching-guide link | PBI-002-01 AC1-3 tests; `sdd check` has no broken link | Validated |
| B02 (RT38, RT42) refuse stale or unproved cards | PBI-002-02 AC1-4 tests | Validated |
| B03 (RT38) `item next` on a clean tree | PBI-002-03 AC1-2 tests, temporary repository with bare remote | Validated |
| B04 (RT38) merged check, guard, forbidden git | PBI-002-03 AC3-6 tests | Validated |
| B05 (RT42, RT36) job `quality`, hardened | PBI-002-04 AC1-4, 6, 7 tests; AC5 manual, below | Validated, with the limitation above |
| B06 (RT38) rationale required | PBI-002-05 AC1-4 tests; `sdd new --help` states the rule | Validated |
| RT42 blocking pipeline | PR #7: `quality` red (help test failed on ANSI codes), fix pushed, `quality` green | **Partial**: red and green proved; the merge is not blocked |
| RT38 per-card record | `progress.yaml` plus `sdd item status 002` | Validated |
| RT36 no secrets | workflow has none, read-only token | Validated |

Manual proof of PBI-002-04 AC5: PR #7 (`feat/002-05-a-rationale-is-required-for-every`) gave a
real red run (commit `5978594`, test `test_new_help_says_the_rationale_is_mandatory`) and a green
run after the fix (commit `9ad031f`). We did not push a deliberate error. Run links to be added
by a person from the PR's Checks tab.

## Documentation upkeep

- [x] ADRs created or superseded
- [x] Architecture pages and diagrams (with official logos)
- [x] Root README (and `poetry run sdd sync` run)
- [x] Component READMEs and CONTRIBUTING
- [x] Teaching guide complete

## Build log

Five cards, one pull request each (#3 to #7), built in backlog order. Notable episodes: `sdd item next` failed once because `progress.yaml` had uncommitted changes that
conflicted with `main` (fixed by restoring the file and syncing); the first `item verify` of
card 05 failed on format and lint and passed on the second run; CI failed once on card 05 (ANSI
codes in a help test), fixed in one commit. No task reached the loop limit of 3 failures. The
ADR number in card 05 was off by one (see the code review).

## Review notes (optional)

Conditions for the merge: none. Decisions worth remembering: branch protection is unavailable
on the free plan; revisit when the plan or the visibility changes.
