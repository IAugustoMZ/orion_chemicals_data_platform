# ADR-0028: Writer choice after the throughput spike (draft for card 15 of 001)

- **Status:** Proposed
- **Date:** 2026-11-13
- **Dossier:** specs/003-tssource-skeleton-spike
- **Requirements:** RT28, RT29; follows [ADR-0027](0027-benchmark-measures-per-second-rates-with-a-bounded-queue.md)

## Context

Card 02 of dossier 003 asked whether Python can sustain 25,000 events/s in backfill. It ran
`tssource bench` for 60 s per format inside the hardened container (read-only, non-root, one bind),
with throwaway random-walk data (2,050 tags, one value per tag per tick) on one developer laptop.
The numbers are in `specs/003-tssource-skeleton-spike/evidence/`.

| Format | Mean events/s | p50 | p95 | Minimum | CPU s per 60 s | Peak MB | Floor held |
|---|---|---|---|---|---|---|---|
| `jsonl-gzip` | 128,979 | 153,750 | 153,750 | 102,500 | 62.4 | 95 | yes, 5.2x |
| `jsonl` | 422,813 | 410,000 | 512,500 | 307,500 | 40.1 | 96 | yes, 16.9x |
| `parquet` | 1,393,146 | 1,383,750 | 1,640,000 | 973,750 | 25.2 | 117 | yes, 55.7x |

Rates move in steps of one block (51,250 events), so p50/p95/p99 are coarse; the minimum second
still beat the floor in every run. The bottleneck label was `writing` in all three runs: the
vectorised numpy generator always outran the serialiser, so the label is relative (who waited),
not a verdict that writing is slow.

## Decision (proposed)

Python is fast enough: the generator does **not** need a process pool or a faster language to
meet RT29 in backfill. Card 15 of 001 should start from **Parquet by row group** as the default
file writer, because it is the fastest and the cheapest in CPU, and keep **gzip JSON Lines** as
the fallback when a human-readable file is required. This is a proposal: the final layout, the
real signal model (which will cost far more than a random walk) and the real-time writer are
still to be measured by their own cards.

## Alternatives considered

| Option | Result in the spike | Verdict |
|---|---|---|
| Parquet by row group | 1.39 M events/s, lowest CPU | proposed default |
| Plain JSON Lines | 0.42 M events/s | readable, large files; fallback |
| gzip JSON Lines | 0.13 M events/s, most CPU | slowest, still 5x above the floor |
| `multiprocessing` writer | not needed by these numbers | rejected for now (ADR-0027) |

## Consequences

- + RT29 is answered with a measurement: the floor held in every second of every run.
- + The ports of card 02 (`EventSource`, `EventSink`) are enough to swap formats later.
- − The margin shrinks when real signals (noise, quality codes, exceptions) replace the random
  walk; card 15 must repeat the measurement with the real generator.
- − One laptop, one run per format: revisit if two runs differ by more than the spread we accept.
