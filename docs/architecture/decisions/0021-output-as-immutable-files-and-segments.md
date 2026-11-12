# ADR-0021: The output is a folder of immutable files, with small stream segments

- **Status:** Proposed (the serialiser and thread layout are confirmed by the spike of card 04; this ADR is then updated and accepted)
- **Date:** 2026-11-12
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT28, RT29, RT23

## Context

There is no broker yet (out of scope), so the interface to the next feature is a local folder. A
reader must be able to read while the generator writes, must see data within seconds in real
time, and must be able to tell that a piece is missing. The event rate and delay targets come
from commercial references and must be measured, not assumed.

## Decision

- The stream is written as gzip **JSON Lines segments** `stream/<site>/<date>/<hh>/<seq>.jsonl.gz`,
  closed every few seconds (a setting). A segment appears under its final name only when complete,
  never changes, and numbers have no gaps. `.done` holds the final count when the hour is closed.
- Tables (archive, catalogue, truth) are **Parquet**. Closed days are never rewritten.
- Writing uses a temporary name and `os.replace`.
- Writers run behind a bounded queue; a full queue makes the producer wait, and the wait is
  counted. Nothing is dropped silently.
- The serialiser (gzip JSON Lines, plain JSON Lines, Parquet by row group) and the thread layout
  (generation thread plus writer threads, or processes) are chosen by the spike with measured
  numbers, and the winner is recorded here.

## Alternatives considered

| Option | Delay | Detects a missing piece | Why it lost (or won) |
|---|---|---|---|
| One file per hour | up to an hour | no | fails the delay target |
| One growing file | seconds | no | readers see partial lines |
| Message broker | seconds | yes | out of scope; a later dossier |
| Immutable segments with a marker (this ADR) | seconds | yes | won |

## Consequences

- + A consumer can poll the folder safely and detect gaps.
- − Many small files; the segment length is a trade-off between delay and file count and is
  reported by the trial.
- Revisit when a broker replaces the folder.
