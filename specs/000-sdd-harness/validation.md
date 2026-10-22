# Validation · 000 · The SDD harness

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

The recorded G5 needs `poetry run sdd verify 000`, which refuses until G4 has passed
(`error: G5 needs G1 passed; it is pending`, by design). During the build every check of
[checks.yaml](../../harness/checks.yaml) was run directly, on Windows 11, Python 3.11.9,
Poetry 2.3.4, on 2026-10-21:

| Check | Tool (version) | Result |
|---|---|---|
| format | ruff 0.17.1 | pass |
| lint | ruff 0.17.1 | pass |
| types | mypy 1.20.2, strict | pass (59 source files) |
| architecture | import-linter 2.15 | pass (3 contracts kept) |
| tests | pytest 9.1.1 + pytest-cov 7.1.0 | pass: 116 tests, 96.0 % branch coverage (threshold 85 %) |
| security | bandit | pass (no issue) |
| secrets | detect-secrets 1.5.0 | pass (baseline has no finding) |
| dependencies | pip-audit 2.10.1 | pass (no known vulnerability) |
| harness | sdd check | pass (0 findings) |
| docs-site | mkdocs 1.6.1 + Material 9.7.7, `--strict` | pass |

TODO(sdd): After G4, run `poetry run sdd verify 000` and paste its result here (commit, date,
verdict per check).

## Code review

Self-check by the building agent (not a substitute for the independent review):

- Every module, class and function has a docstring (ruff `D` rules pass); signatures fully typed
  (mypy strict).
- Complexity ≤ 8 per function (ruff `C90`); the longest module is the CLI (about 210 lines, one
  command per function).
- Typed errors only; no bare `except`; `SddError` is mapped to exit code 2 in one place.

TODO(sdd): Independent review by a separate session acting as the
[reviewer](../../harness/roles/reviewer.md), against the checklist in
[quality.md](../../harness/quality.md#3-code-review-checklist); then our own reading of the diff.

## Architecture review

Self-check: the tree matches the plan's file list and the module map in
[docs/architecture/README.md](../../docs/architecture/README.md); the three layer contracts hold;
adapters are instantiated only in `bootstrap.py`; the only module outside clean architecture is
the agent guard, by design (standard library only, ADR-0007 consequences). Diagrams carry the
official logos (`sdd check` reports no `mermaid-logo` finding) and all 15 Markdown files with
diagrams render with Mermaid's own renderer.

TODO(sdd): Independent architecture review (reviewer role) and ours.

## Security review

Self-check of the STRIDE rows of [spec.md](spec.md#security-and-threat-model):

- Spoofing (agent approves): refused without a TTY (tests) and blocked live by the agent guard in
  this Claude Code session (a harmless `echo "sdd approve ..."` was blocked with the ADR-0003
  message).
- Tampering (approvals, guardrails): guard tests pass; the permission rule on
  `deploy/secrets/**` blocked this agent itself from writing a README there (the register moved
  to `docs/architecture/secrets.md`).
- Repudiation: approvals round-trip with member, time, digest, identity, note.
- Information disclosure: detect-secrets clean; secrets paths git-ignored and guarded.
- Elevation: no shell in any subprocess; `yaml.safe_load` only; bandit clean.
- Container: docs service runs as uid 10001, read-only root filesystem and mounts, no
  capabilities, loopback port, healthy.

TODO(sdd): Independent security review (reviewer role) and ours.

## Functional validation

| Behaviour or RT | How validated | Result |
|---|---|---|
| B01, B02 (`sdd new`) | dossier 000 created with `sdd new`; CLI tests; unknown RT refused | pass |
| B03, B04 (states, digests) | 7 gate-state tests; stale-after-edit test | pass |
| B05, B06 (approval rules) | approval tests; `sdd approve` refused without TTY | pass |
| B07 (`sdd verify`) | refuses before G4 (live); verification tests with fake runner; real runner tests incl. batching of long file lists | pass |
| B08 (commit guard) | `sdd guard-commit tools/sdd/bootstrap.py` on this branch → exit 1 "G4 is blocked"; docs-only → exit 0 | pass |
| B09, B10 (`sync`, `check`) | adapters generated for 14 skills and 10 roles; drift detected after editing a role, fixed by `sdd sync`; check found 12 real logo findings on first run, 0 after fixes | pass |
| B11 (agent guard) | 16 guard tests; live block in this session | pass |
| B12 (site) | `mkdocs build --strict`; `docker compose up --build docs` → HTTP 200, healthy | pass |
| B14 (one gate at a time) | `written-ahead` tests (flagged / in order); live: `sdd check` flags dossier 000 for G2, G3, G4, G6 artifacts; the review protocol is a skill, exercised with us at G1 | pass |
| B13 (outside the catalogue) | `TestContext` (rationale missing / present, per kind); PRD text, board label and matrix section tests | pass |
| RT36, RT38, RT42 (spirit) | see security review and G5 table | pass |

TODO(sdd): Our walk-through of the three PRD scenarios (approve a gate, watch an agent be
refused, follow the learning path on the site).

## Documentation upkeep

- [x] ADRs created or superseded (0001-0015)
- [x] Architecture pages and diagrams (with official logos)
- [x] Root README (and `poetry run sdd sync` run)
- [x] Component READMEs and CONTRIBUTING
- [x] Teaching guide complete

## Build log

Honest history of the build loop (no `sdd verify` loop was possible before G4; each check was
run directly):

1. `ruff ^0.8` resolved to an old release; the ranges were widened and the tools upgraded
   (ruff 0.17, pytest 9); the newer rules found 10 test-style issues, fixed or ignored with a
   documented reason in `pyproject.toml`.
2. `sdd check` first run: 1 error, 11 warnings of `mermaid-logo`. Seven were real (nodes naming
   Git, Docker, Python, Claude Code without a logo); two were false positives on file names
   (`mkdocs.yml`, `CLAUDE.md`). The rule now ignores path-like tokens (new test).
3. `mkdocs build --strict`: three links used `#code-review-checklist`; the real anchor is
   `#3-code-review-checklist`. Fixed.
4. bandit misread the reasons written after `# nosec` as test ids; reasons now follow a second `#`.
5. The OpenAI logo was removed from the live Simple Icons CDN (HTTP 404); the registry pins a
   Simple Icons release for it.
6. A semicolon in a sequence-diagram message broke one diagram (Mermaid statement separator).
7. Windows: `detect-secrets` arguments with `^` and `|` were mangled by the command shim; long
   file lists could exceed the command-line limit, so the check runner now batches them.
8. The agent's own permission rule blocked writing `deploy/secrets/README.md`; the register was
   moved to `docs/architecture/secrets.md` (the guardrail is right; the document was misplaced).
9. Our first question after the build: "how do I start a CRUD that is not in the requirements,
   without naming RTs?" G0 demanded an RT for every feature, and the docs showed commands as
   if we had to pick RTs. Fixed by ADR-0014 (B13): the agent maps plain requests, and a feature
   may be outside the catalogue with a rationale.
10. Our first approval attempt (G1) was refused for a `TODO(sdd)` in "What we agreed at G1", a
    section the agent had left for us to write although it had drafted everything else. That is
    ceremony: the approval already records who, when and which exact text. The section became
    "Review notes (optional)" without a placeholder (PRD and validation templates).
11. Checking G2 and G4 the same way found two more false refusals: `backlog.md` and `spec.md`
    only *mention* the marker in prose. Readiness now ignores a marker quoted in inline code
    (new test); a mention inside a diagram of a G6 file was reworded.
12. Our second finding: the agent had drafted every phase before we reviewed the first, so
    approving would be a rubber stamp (automation bias), and nothing shows we read anything.
    Fixed by ADR-0015 (B14): one gate at a time, a review conversation in the chat (skill
    `sdd-review-gate`), approval still at the terminal, and a `written-ahead` warning in
    `sdd check`. Dossier 000 itself triggers that warning for G2, G3, G4 and the teaching
    guide, honestly: it was written ahead during the bootstrap. We review it gate by gate
    in the chat.

## Review notes (optional)

_Nothing needed to approve. Add a line here (or use `--note` when approving) only for a
condition on the merge or a decision worth remembering._
