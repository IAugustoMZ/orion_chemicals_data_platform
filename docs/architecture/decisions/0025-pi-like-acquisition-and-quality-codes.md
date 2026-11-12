# ADR-0025: The output has the shape of a historian: exception, snapshot, compression, quality codes

- **Status:** Proposed (the exact quality sub-reasons are confirmed by card 13)
- **Date:** 2026-11-12
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT17, RT23, RT28

## Context

A historian does not keep every scan. A platform tested on raw samples at every tick would meet
neither the event rates nor the gaps, bad values and late bursts of real data. The rates in the PRD
(5 to 50 events/s per 1,000 tags) describe the data after the reductions of a historian.

## Decision

- An **exception filter** per tag decides what the collector sends (deviation, minimum and maximum
  time). The result is the stream.
- A **snapshot** per tag keeps the latest event; a **swinging-door compression** (deviation, minimum
  and maximum time) decides which snapshots are written to the archive; digital tags archive every
  change. Each archive record lists the stream events that justify it.
- Quality is `Good`, `Uncertain` or `Bad` with a reason (for example sensor failure, last usable
  value, engineering units exceeded). A bad digital value carries a state text such as
  `Bad Input`. Report-by-exception and lab tags have no expected frequency, which is what RT17 needs.
- Out-of-order events bypass compression, as a real buffer subsystem does.
- Faults are injected before the exception filter and are always labelled in `truth/`.

## Alternatives considered

| Option | Realistic shape | Event rate in the PRD band | Why it lost (or won) |
|---|---|---|---|
| Raw samples at every tick | no | no (far above) | not what a historian holds |
| Fixed downsampling | partly | partly | no exceptions, no fidelity bound |
| Exception, snapshot, swinging door (this ADR) | yes | yes | won |

## Consequences

- + The output can be read as a historian export; reconstruction error is bounded by `compdev`.
- − The swinging door is sequential per tag; the spike decides how to parallelise it.
- − Quality codes are a small subset of PI and OPC UA; richer codes need a new ADR.
