# Validation · 003 · Generator skeleton and throughput spike

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

`poetry run sdd verify 003` passed at commit `fe44586` (main after PR #15, 2026-11-13). Ten of
ten checks PASS: format, lint, types, architecture (import-linter), tests (coverage above the
85% threshold), security (bandit), secrets (detect-secrets), dependencies (pip-audit), harness
(`sdd check`) and docs-site (mkdocs strict). Both cards were also verified with
`sdd item verify` before their pull requests (#12 and #13) and merged by a person.

## Code review

Independent review by the `reviewer` subagent (a session that did not write the code). No
blockers. Findings and their handling:

| # | Where | Finding | Severity | Handling |
|---|---|---|---|---|
| 1 | ADR-0027 line 19 | "The stage that waited longer is the bottleneck" reads backwards; the code (full queue = WRITING) is right | major (document) | Resolved: ADR-0027 sentence amended (wording only, code unchanged) |
| 2 | `bench --seconds` | Spec DoS row claims a bound, but only `min=1` exists | major (spec vs code) | Resolved: PR #15 adds `max=3600` and a test (AC3) |
| 3 | `RunBenchmark.run` `finally` | `sink.close()` failure is not wrapped in `TssourceError` and can mask an earlier error | minor | Accepted for the spike; candidate for card 15 of 001 |
| 4 | `run_bench`, `bench` | Unwritable output folder gives a traceback, not a one-line error | minor | Accepted for the spike; candidate for card 15 of 001 |
| 5 | `_write_loop` | Blocks written after the deadline are not counted, so `events` slightly understates | minor | Accepted; limitation noted in ADR-0028 context |
| 6 | bottleneck tie | `full == empty` gives GENERATION | nit | Accepted; documented in the teaching guide |
| 7 | `test_queue_depth_never_exceeds_its_bound` | Bound is structural (`queue.Queue(maxsize)`) | nit | Accepted; test still checks the queue really fills |
| 8 | `run_bench` | Does scratch handling beyond wiring | nit | Accepted; small |
| 9 | `app.py` imports | `health` and `--help` load pyarrow | minor | Accepted for now; lazy import is a follow-up |
| 10 | Dockerfile idle path | SIGTERM ignored by PID 1, `docker stop` waits 10 s | nit | Accepted; `init: true` is a follow-up |
| 11 | `_State.__init__` | Missing docstring | nit | Accepted; fix with the next code change |

Found fine: percentile maths and the empty-input error, pure `Distribution`/`BenchResult`,
mean-only floor, bounds-checked bucketing, `bench.json` version 1, sinks rejecting a foreign
block, deterministic numpy source, frozen `Settings`, honest probe on Windows, docstrings that
state the why.

## Architecture review

Sound. `domain` imports only errors and stdlib; `application` imports only `domain` and its
ports are Protocols; `infrastructure` holds numpy, pyarrow and stdlib adapters; the CLI reaches
adapters only through `bootstrap`. Import-linter keeps all contracts and `test_layers.py`
proves they bite. Threading is correct: one writer per counter, a writer failure stops the
producer, a producer failure lets the writer drain, the writer is always joined. ADR-0027 (Accepted)
and ADR-0028 (Proposed) exist and are indexed; deployment page and READMEs were updated.
RT01 holds: the `docs` service is untouched and `tssource` is a separate service and group.

## Security review

| STRIDE row | Verdict |
|---|---|
| Tampering | OK: read-only root filesystem, one writable bind, tmpfs `/tmp` (compose test) |
| Elevation | OK: user 10001, `cap_drop ALL`, `no-new-privileges`, no ports |
| Information disclosure | OK: no credential read or logged; base image pinned by digest |
| Denial of service | OK: queue bound, scratch cleanup and `--seconds` capped at 3600 (PR #15) |
| Input validation | OK: `Settings` validates env, `--format` is a closed enum, errors are one line |
| Secrets (RT36) | OK: detect-secrets test passes, nothing under `deploy/secrets/` touched |

## Functional validation

| Behaviour or RT | How validated | Result |
|---|---|---|
| PBI-003-01 AC1-AC5 (package, CLI, container, gates) | `@pytest.mark.ac` tests in `test_cli`, `test_compose_hardening`, `test_layers`, `test_no_secrets` | Pass |
| PBI-003-02 AC1 (distribution, `bench.json`) | `test_benchmark.py` unit and real-adapter tests | Pass |
| PBI-003-02 AC2 (bounded queue) | `test_queue_depth_never_exceeds_its_bound` | Pass |
| PBI-003-02 AC3 (bottleneck named, exit 3) | fakes for both stages, failing sink, CLI exit 3 | Pass |
| PBI-003-02 AC4 (same seed, same events and files) | seed and file-bytes tests | Pass |
| RT29 (25,000 events/s floor) | three real 60 s runs in the hardened container, `evidence/bench-*.json` | Held: 128,979 / 422,813 / 1,393,146 events/s (5.2x / 16.9x / 55.7x) |
| RT28 (generator skeleton) | `tssource health`, `run`/`config`/`report` exit 1 with a one-line message | Pass |
| RT01 (read-only access), RT36 (no secrets) | compose test, detect-secrets, diff review | Not broken |

Exploratory notes: peak memory is 0.0 on Windows and real only in the container; rates move in
steps of one 51,250-event block; the 60 s container runs have no automated test (stated in the
teaching guide). One laptop, one run per format.

## Documentation upkeep

- [x] ADRs created or superseded (0027 Accepted, 0028 Proposed)
- [x] Architecture pages and diagrams (with official logos)
- [x] Root README (and `poetry run sdd sync` run)
- [x] Component READMEs and CONTRIBUTING
- [x] Teaching guide complete

## Build log

Card 01: built, verified, PR #12 merged. Card 02: one `sdd item verify` failure on `format`
(an edit after formatting), fixed with `ruff format` and re-verified; fewer than three
consecutive failures, so no escalation. Other fixes: a SyntaxError from a newline escape in
`app.py`; a bottleneck test that needed a real short sleep in slow fakes (limited to costly
stages so tests stay fast); ruff E501 and mypy typing of `GzipFile` and pyarrow calls; a
mangled Windows path when running docker from Git Bash (`MSYS_NO_PATHCONV=1`). Card 02 merged
as PR #13. A leftover local git stash from card 01 is harmless and was left untouched.

## Review notes (optional)

Decided by us (recommendations accepted): ADR-0027 wording amended; `--seconds` gets an upper
bound of 3600 in a small follow-up PR, merged as PR #15.
