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

After G4 passed, `poetry run sdd verify 000` ran at commit `64e8362` with the build of tasks T17
to T22 in the working tree: all ten checks passed (format, lint, types, architecture, tests,
security, secrets, dependencies, harness, docs-site) and G5 showed *passed* (133 tests, 96.4 %
branch coverage). It ran again on 2026-11-04 after the fixes of the independent review (see
"Code review"): all ten checks passed again. The table above is the earlier direct run, kept
as history.

Manual evidence of the two behaviours that `sdd verify` does not cover:

- **B17 (pre-commit):** `poetry run pre-commit run --all-files` on 2026-10-28: all 16 hooks
  passed (whitespace, yaml, toml, merge conflicts, large files, line endings, `sdd guard-commit`,
  ruff format and check, mypy, import-linter, pytest, detect-secrets, `sdd sync`, `sdd check`).
- **B12 (site in Docker):** `docker compose up --build -d docs` on 2026-10-28: the container
  became healthy, `http://127.0.0.1:8000/` returned HTTP 200, `/docs/architecture/` returned the
  page with 3 Mermaid blocks and the new ADR-0018 page returned 200. The diagrams are drawn by
  the browser; I checked that the blocks are served, not the rendered picture, so the visual
  check stays for our walk-through below.

## Code review

Self-check by the building agent (not a substitute for the independent review):

- Every module, class and function has a docstring (ruff `D` rules pass); signatures fully typed
  (mypy strict).
- Complexity ≤ 8 per function (ruff `C90`); the longest module is the CLI (about 210 lines, one
  command per function).
- Typed errors only; no bare `except`; `SddError` is mapped to exit code 2 in one place.

**Independent review** by the `reviewer` subagent (a separate agent from the one that built the
change), 2026-11-04, against the checklist in
[quality.md](../../harness/quality.md#3-code-review-checklist). Verdict: **approve with
conditions**; no blockers. It re-ran `sdd check` (0 findings), pytest (133 passed, 96.40 %
branch coverage), ruff, mypy strict, import-linter (3 contracts kept) and bandit: all clean.

| Id | Severity | Finding | Status |
|---|---|---|---|
| C1 | major | `_run` in `tools/sdd/interfaces/cli/app.py` catches only `SddError`; the `OSError` re-raised when scaffolding fails gives a traceback and exit 1 instead of `error:` and exit 2 (B19). Fix: wrap it in an `SddError` subclass and add a CLI test. | fixed: `_run` maps `OSError` to `error:` and exit 2; CLI test `test_failed_scaffolding_exits_with_2_and_an_error_line` |
| C2 | minor | `add_artifacts` records a file as written only after `write_text`, so a mid-write failure leaves a partial file; "never overwrite" is check-then-write. Fix: open with mode `"x"` and register before writing. | fixed, with test `test_add_artifacts_removes_a_partially_written_file` |
| C3 | minor | `CreateDossier` creates the dossier, then scaffolds `prd.md`; a failure in between leaves a dossier without a PRD and a burned id. | open: fixing it changes `ScaffoldArtifacts.for_creation`, which the approved spec's class diagram shows; left for a decision (record as accepted or amend the spec) |
| C4 | minor | `input()` in the confirmation adapter raises on Ctrl-D and Ctrl-C (traceback). | fixed for Ctrl-D (a "no", tested); Ctrl-C keeps Typer's own "Aborted!" |
| C5 | minor | Test gap: no `CheckHarness` test with a dossier that has only `prd.md`, none for the partial write (C2) or the CLI failure path (C1). | fixed: the partial write (C2), the CLI failure path (C1) and Ctrl-D (C4) have tests; a dossier with only its PRD is covered by `test_work_in_order_is_not_flagged` |
| C6 | nit | `except Exception: save(...); raise` in `ApproveGate` masks the original error if the undo itself fails. | fixed: the undo failure is raised `from` the original error |
| C7 | nit | This file dates the post-G4 `sdd verify` run 2026-10-28; `dossier.yaml` records 2026-11-04. Align the dates and re-run pre-commit. | dates aligned; the pre-commit run of 2026-10-28 below is still to be repeated by us |

The reviewer confirmed that every behaviour of the spec has code and tests, that docstrings
state the why and the contract, and that nothing beyond the spec was built.

Our own reading of the diff is recorded under "Review notes" below.

## Architecture review

Self-check: the tree matches the plan's file list and the module map in
[docs/architecture/README.md](../../docs/architecture/README.md); the three layer contracts hold;
adapters are instantiated only in `bootstrap.py`; the only module outside clean architecture is
the agent guard, by design (standard library only, ADR-0007 consequences). Diagrams carry the
official logos (`sdd check` reports no `mermaid-logo` finding) and all 15 Markdown files with
diagrams render with Mermaid's own renderer.

**Independent review** by the `reviewer` subagent, 2026-11-04. Verdict: **approve**. Layers
hold (3 contracts kept), ports are Protocols, wiring is only in `bootstrap.py`, the plan's file
list matches the tree, ADRs 0016 to 0018 match the code, and no diagram lacks a logo.

| Id | Severity | Finding | Status |
|---|---|---|---|
| A1 | minor | `docs/architecture/README.md` module map does not list `ScaffoldArtifacts` or the `add_artifacts` port method; `sdd check` cannot detect it. | fixed (node added to the diagram) |
| A2 | nit | `harness/how-it-works.md` still shows the obsolete `echo "001 G4" \| sdd approve`; it should be `echo y \|`. | fixed |
| A3 | nit | `ApproveGate` depends on the concrete `ScaffoldArtifacts`, not a Protocol (acceptable inside one layer; ADR-0018 records it). | accepted by design |

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

**Independent review** by the `reviewer` subagent, 2026-11-04, probing `agent_guard.decide()`
directly. Verdict: **approve with conditions** (S1 and S2 are real gaps against B11, to fix or
to accept explicitly as residual risk). The STRIDE rows for spoofing, scaffolding tampering,
command injection (no `shell=True`), unsafe YAML and slug/template input held.

| Id | Severity | Finding | Status |
|---|---|---|---|
| S1 | major | The guard does not block `git commit -n`, `SKIP=... git commit`, `git -c core.hooksPath=... commit`, `git push origin +main`, or `python -m sdd.interfaces.cli.app approve`. (The TTY test still stops the last one.) | open, for our decision |
| S2 | major | `.claude/settings.local.json` (can disable hooks), `.git/hooks/`, `.secrets.baseline`, `harness/checks.yaml` and `pyproject.toml` are not guardrail files. | open, for our decision |
| S3 | minor | The secrets rule covers file tools only: `cat .env` through Bash and the Grep and Glob tools pass. Fix the guard or reword the STRIDE row. | open |
| S4 | minor | The guard fails open on malformed input or an internal error. | open |
| S5 | minor | ADR-0016 and the adapter docstring overstate "neither a pipe nor a typed phrase can reach the prompt": a pseudo-terminal wrapper creates a TTY. Reword; optionally refuse when agent environment variables are set. | reworded in ADR-0016 and the adapter docstring; the optional refusal is not built |
| S6 | minor | All approvals record `git_identity: (git identity not configured)`. Set `git config user.name` and `user.email` before approving G6. | open |

The guard files (`tools/agent_hooks/`, `.claude/settings.json`) are ones agents may not edit, so
S1 to S4 need our own change or an explicit acceptance of the risk.

## Functional validation

| Behaviour or RT | How validated | Result |
|---|---|---|
| B01, B02 (`sdd new`) | dossier 000 created with `sdd new`; CLI tests; unknown RT refused | pass |
| B03, B04 (states, digests) | 7 gate-state tests; stale-after-edit test | pass |
| B05, B06 (approval rules) | approval tests; only `y`/`yes` approves (`test_terminal_accepts_only_yes`); refused without a TTY and by the agent guard | pass |
| B01, B19 (files as gates pass) | `test_artifacts_after_each_gate`; first approval creates nothing, second creates the next gate's files, existing files never overwritten, failed scaffolding undoes the approval (use case and adapter); CLI prints `created:` lines | pass |
| B15 (backlog card) | `test_every_card_field_is_a_required_placeholder` | pass |
| B07 (`sdd verify`) | refuses before G4 (live); verification tests with fake runner; real runner tests incl. batching of long file lists | pass |
| B08 (commit guard) | `sdd guard-commit tools/sdd/bootstrap.py` on this branch → exit 1 "G4 is blocked"; docs-only → exit 0 | pass |
| B09, B10 (`sync`, `check`) | adapters generated for 14 skills and 10 roles; drift detected after editing a role, fixed by `sdd sync`; check found 12 real logo findings on first run, 0 after fixes | pass |
| B11 (agent guard) | 16 guard tests; live block in this session | pass |
| B12 (site) | `mkdocs build --strict`; `docker compose up --build docs` → HTTP 200, healthy | pass |
| B14 (one gate at a time) | `written-ahead` tests (flagged / in order); live: `sdd check` flags dossier 000 for G2, G3, G4, G6 artifacts; the review protocol is a skill, exercised with us at G1 | pass |
| B13 (outside the catalogue) | `TestContext` (rationale missing / present, per kind); PRD text, board label and matrix section tests | pass |
| RT36, RT38, RT42 (spirit) | see security review and G5 table | pass |

**Our walk-through** of the three PRD scenarios (approve a gate, watch an agent be refused,
follow the learning path on the site): the mentor reports having tested these behaviours before
G6, on 2026-11-04. The steps and observations were not written down at the time, so this file
records the claim, not the evidence; the automated evidence is in the table above.

## Documentation upkeep

- [x] ADRs created or superseded (0001-0018; 0016 to 0018 accepted)
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

13. After G4 the three decisions of the G3 and G4 reviews were built test first: the `y/N` prompt
    (ADR-0016), files created as gates pass with the undo on failure (ADR-0018) and the backlog
    card test (ADR-0017). The new tests failed first, as intended. Two slips of mine were caught
    by the suite or the linter (a wrong state in one new assertion, an overly broad
    `pytest.raises`). `sdd verify 000` passed on its first run.

## Review notes (optional)

_Nothing needed to approve. Add a line here (or use `--note` when approving) only for a
condition on the merge or a decision worth remembering._
