# PRD · 003 · Generator skeleton and throughput spike

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/003-tssource-skeleton-spike/` · branch `spec/003-tssource-skeleton-spike` · kind **feature** · created 2026-11-13.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT28 | P | Sizing shall declare tags, frequencies, average size, history, concurrency and growth, separating measurement from projection. | A capacity spreadsheet with traceable inputs and a matching test. |
| RT29 | P | The prototype shall measure sustained throughput, load duration, delay between availability and publication, and resources used. | A trial on the chosen slice with the distribution and the p95, not only the mean. |

**What this means in plain words.** This dossier is the first child of umbrella dossier 001 (the
global plant data generator, package `tssource`). It delivers cards 03 and 04 of 001. First, an
empty but complete package that is built, typed, linted, tested and runs in a hardened
container. Second, a spike that measures, before anything else is built on it, whether Python
can write 25,000 events/s and with which file format. The measured numbers are the first honest
inputs for RT28 (separating measurement from projection) and RT29 (distribution and p95, not
the mean). The full sizing report and the delay between availability and publication stay in
001's later cards, because delay needs the real-time writer that does not exist yet.

**Related RTs left out.** RT02, RT07, RT09, RT12, RT17, RT23, RT38, RT39, RT40 belong to the
other children of 001. RT30 (industrial capacity) is not claimed: this measures the generator,
not the platform.

**RTs this work must not break.** RT01 (nothing here can command a system; the container is
read-only and publishes no port) and RT36 (no credentials in code, compose or output).

## Problem

The team will build twenty more cards of the generator. If the package layout, the quality
gates and the container are decided card by card, each card pays for it again, and the layers
drift. If Python turns out unable to write 25,000 events/s, we learn it after the signal model,
the faults and the archive exist, and the generator becomes the limit of every platform test we
planned. Both are cheap to settle first and expensive to settle late. Today neither is settled:
nothing of the generator exists and no number about its speed exists.

## Goals and success metrics

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| A skeleton every later card reuses | quality gates that include `tssource`; commands listed by `--help`; container hardening flags | no package | mypy, ruff, import-linter, bandit, pytest and detect-secrets all cover `tssource`; `run`, `bench`, `config`, `report`, `health` listed; read-only root, no capability, non-root, no port | `sdd verify 003`; a test of `--help`; a test that parses `compose.yaml` |
| Know whether Python meets the rate | sustained events/s in backfill, as mean, p50, p95, p99 and minimum per second of wall time; CPU seconds; peak memory | none | the 25,000 events/s floor held for a 60-second run, or the bottleneck stage named; 150,000 events/s reported only | `tssource bench` writes `bench.json`; run inside the container |
| Choose the writer on evidence | serialisations compared (JSON Lines gzip, JSON Lines plain, Parquet by row group) and one thread layout | none | one table of numbers, same seed and events for all; the winner recorded for the writer card (001 card 15) | `bench.json` of each variant; a test that two runs with one seed produce the same events |

## Users and scenarios

- **Mentee (builds the cards).** Runs `poetry install --with tssource` and `tssource --help`,
  and finds the layers, the settings object and the composition root already in place. A wrong
  import from `domain` into `numpy` fails `lint-imports`, so the layer rule is felt on day one.
- **Mentor (decides the design).** Reads `bench.json` and the comparison table, and decides
  whether the writer design stands or the 25,000 events/s floor must be revisited before more is built.
- **Later cards of 001 (the consumers).** Reuse the package, the settings, the quality gates and
  the benchmark use case, and read the recorded winner as input to the file-layout card.

## Scope

### In scope

- Cards 03 and 04 of umbrella 001, built one per branch with the flow of dossier 002.
- The `tssource` package with four layers and a composition root, a base error, an immutable
  `Settings` read once, and a Typer CLI whose commands other than `health` say "not implemented".
- The dependency group, the quality-gate configuration, the image and the compose service.
- The benchmark: a vectorised block generator for 2,050 random-walk tags, three serialisers,
  a bounded writer queue, a distribution value object, CPU and memory probes, and `bench.json`.

### Out of scope

- Any realism of the signal, the plant model, faults, time zones or the final file layout.
- The real-time writer, the heartbeat behind `health` and the delay measurement (later cards).
- The sizing spreadsheet and the full RT28/RT29 report (001, card 21).
- Kafka, an HTTP API, and consuming the data.

## Constraints and assumptions

- Local only (Docker Compose); Poetry only; English only; no credentials (RT01, RT36).
- The quality bar is the one of `sdd`: mypy strict, ruff, import-linter, bandit, detect-secrets,
  pip-audit, docstrings on everything, tests with the code.
- Assumption: this machine is the measurement base; numbers are valid for it and are never
  extrapolated to a platform claim (RT30).
- Assumption: numpy and pyarrow wheels exist for our Python and a slim Linux base image; checked
  in the specification.
- Assumption: the 60-second run is long enough to show a stable rate; the specification may lengthen it.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| Python cannot sustain 25,000 events/s | the generator would limit every later test | that is what the spike measures; the exit code and the named stage give the evidence, and we decide next steps together (owner: mentor) |
| A laptop benchmark is noisy, and a container adds overhead | a wrong choice of serialiser | report the distribution, repeat the run, state the machine; do not choose on one run (owner: mentee) |
| Throwaway benchmark code becomes the real writer by habit | weak design carried forward | the spike has its own use case and ports; card 15 adopts or replaces it explicitly (owner: mentee) |
| Open question: is 60 seconds enough, and is the floor for the stream or for backfill only? | wrong target accepted | agree after the first measured run (owner: mentor) |
| New dependency group (numpy, pyarrow, tzdata) enlarges the image and the audit surface | supply-chain exposure | `pip-audit` in the suite, versions pinned by the lock file, no compiler in the final image (owner: mentee) |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
