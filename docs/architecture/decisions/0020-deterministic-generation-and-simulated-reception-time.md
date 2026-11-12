# ADR-0020: Generation is deterministic, and the reception time is simulated

- **Status:** Proposed
- **Date:** 2026-11-12
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT07, RT23, RT28, RT39

## Context

The platform's tests need to repeat a situation exactly: the same faults at the same moments,
the same late burst. Three forces collide. A run in real time, one ahead of the clock and a
backfill of a past period should give the same data. Adding a tag must not change the numbers of
another tag. And the reception time (when the service handled an event) is naturally the wall
clock, which differs on every run.

## Decision

- One `numpy.random.SeedSequence(seed)` is **spawned** with a stable key per site, tag and purpose
  (signal, each fault kind, naming, lab), so a new tag changes nothing else.
- The domain and the generation never read the wall clock. Time is passed in, UTC and aware.
- The **reception time is simulated**: event time plus a seeded transport delay, shifted by
  outages and replay. The real clock appears only in the manifest (attempt times), metrics and the
  real-time pacing.
- The **run id** is `r-` plus 12 hex digits of SHA-256 over seed, configuration digest, versions
  and period. Mode, speed and output folder are not part of it.
- Delay in real time is measured end to end by probe events found in the output folder, not
  by comparing simulated times.

## Alternatives considered

| Option | Identical across modes | Honest delay measure | Why it lost (or won) |
|---|---|---|---|
| Reception time from the wall clock | no | yes | real-time and backfill could never match |
| One shared random generator | no (order matters) | n/a | adding a tag shifts every other |
| Run id with an attempt counter | no | n/a | a repeated run would not give the same id and files |
| Simulated reception time plus probe events (this ADR) | yes | yes | won |

## Consequences

- + Two runs with the same settings give byte-identical data files; tests compare digests.
- + Backfill, accelerated and real time can be compared.
- − "Reception time" in files is a model of transport, not an observation; the delay figures
  come from probes and are reported separately.
- − A change of settings or versions changes the run id by design.
