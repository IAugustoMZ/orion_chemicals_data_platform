# Release and learnings · 003 · Generator skeleton and throughput spike

> **Phase 7 · Release & Learn**, closed by **G7 · Results validated** (both of us approve).
> How to fill this file: [lifecycle, phase 7](../../harness/lifecycle.md#phase-7-release-and-learn).

## Release

| Item | Value |
|---|---|
| Merged work | PR #12 (card 01, skeleton), PR #13 (card 02, spike), PR #15 (`--seconds` max 3600), PRs #14 and #17 (validation, G5 re-verification) |
| Main at G6 | `9595211` |
| Service | `tssource` in `compose.yaml`, image `orion/tssource:local`, built from `docker/tssource.Dockerfile` |
| Commands | `docker compose build tssource`, then `docker compose run --rm tssource <command>` |
| Hardening | read-only root, non-root user 10001, `cap_drop ALL`, `no-new-privileges`, no published port, tmpfs `/tmp`, one writable bind |
| Data migration | none; the `docs` service is untouched (RT01) |

`tssource` is a run-to-completion tool, not a daemon, so "healthy" means `tssource health` exits 0
(the image healthcheck). It was run on 2026-11-13 from the release branch after G6.

## Observation

| What | How obtained | Result |
|---|---|---|
| Image builds | `docker compose build tssource` | Built |
| Settings readable | `docker compose run --rm tssource health` | exit 0 |
| Stub commands | `docker compose run --rm tssource run` | `run: not implemented yet`, exit 1 |
| Post-release smoke benchmark | `bench --seconds 10 --format parquet` in the container | mean 1,183,875 events/s, floor held, bottleneck `writing`, exit 0 |
| Release-gate benchmarks | three 60 s runs, `evidence/bench-*.json` | jsonl-gzip 128,979; jsonl 422,813; parquet 1,393,146 events/s (floor 25,000) |

The smoke run is 10 s on a possibly busier laptop and is lower than the 60 s Parquet run
(1,393,146); it is a sanity check, not a new measurement. There is no telemetry stack for the
generator yet, so observation is by command output only.

## Feedback

Recorded from the reviews and decisions made in the chat; the mentor and mentee may add their
own lines before G7.

- Worked: one command gives a distribution and a named bottleneck; exit code 3 makes the floor
  checkable in scripts; the independent review found a real spec-versus-code gap (finding 2).
- Confused: the bottleneck label is relative (who waited), so `writing` on all three runs reads
  like "writing is slow"; ADR-0028 and the teaching guide explain it, the CLI output does not.
- Missing: a one-line error for an unwritable output folder (finding 4); lazy imports so `health`
  and `--help` do not load pyarrow (finding 9); an automated test of the 60 s container runs.

## Results against the goals

| PRD goal | Result | Evidence |
|---|---|---|
| A skeleton every later card reuses | Met | `sdd verify 003` 10/10 PASS; tests for `--help`, layer contracts and `compose.yaml` hardening; PR #12 |
| Know whether Python meets the rate | Met | 25,000 events/s floor held in every second of every 60 s run (5.2x to 55.7x on the mean); p50/p95/p99/min reported; bottleneck named; RT29 answered for backfill. The 150,000 events/s figure is met by Parquet and plain JSON Lines (report only) |
| Choose the writer on evidence | Met, as a proposal | one table, same seed and events (determinism test); Parquet by row group proposed in ADR-0028 (Proposed) for card 15 of 001 |

Limits: one laptop, one run per format, random-walk data, not the real signal model; the delay
between availability and publication (RT29) needs the real-time writer and stays in 001.

## Learnings

- **Problem:** Python is fast enough for the backfill floor with a vectorised generator and no
  process pool; the margin will shrink with the real signal model, so card 15 must re-measure.
- **Platform:** rates move in steps of one 51,250-event block, so percentiles are coarse; a
  spec claim ("bounded") needs a test that proves the bound, or the review will find it.
- **Harness (proposals, not edits of `harness/`):**
  - A card cannot go from `merged` to `verified` after a follow-up fix on `main`; a small
    "amend a merged card" path would avoid the detour through a docs PR (candidate enabler).
  - Generated files drift after merges; a CI hint saying "run `sdd sync`" would save a round trip.
  - Running docker from Git Bash mangles paths; document `MSYS_NO_PATHCONV=1` for Windows.

## Next items

- ADR-0028: accept or amend it when card 15 of 001 runs the real generator.
- Fix review findings 3, 4, 9, 10 and 11 (error wrapping, one-line errors, lazy imports,
  `init: true`, a docstring) in the next `tssource` card.
- Re-measure with the real signal model and repeat each format at least twice.
- Add the delay measurement once the real-time writer exists (RT29).
