# ADR-0027: The spike measures per-second rates through a bounded queue and exits 3 below the floor

- **Status:** Proposed
- **Date:** 2026-11-13
- **Dossier:** specs/003-tssource-skeleton-spike
- **Requirements:** RT28, RT29; refines [ADR-0019](0019-tssource-package-and-dependencies.md)

## Context

RT29 asks for sustained throughput as a distribution with the p95, not only the mean. The
largest risk of the generator is that Python cannot write 25,000 events/s. We need a measurement
that cannot hide a slow second behind a fast average, that names the slow stage, and that can be
repeated by anyone with the same seed.

## Decision

`tssource bench` counts the events written in every second of wall time and reports mean, p50,
p95, p99 and minimum of those per-second rates, plus CPU seconds and peak memory. One generation
thread feeds one writer thread through a bounded `queue.Queue`; the stage that made the other one wait
more often is the bottleneck (a full queue hit by the producer means writing is the limit, an empty
queue hit by the writer means generation is; counts, not seconds, so the label is deterministic). The minimum and p99 are reported but do not fail the run (decided at G4). If the **mean** rate over the run is below 25,000 events/s the command exits
with code 3 and names the stage. The spike has its own use case and ports (`EventSource`,
`EventSink`, `ResourceProbe`, `Clock`); card 15 of 001 adopts or replaces them explicitly.

## Alternatives considered

| Option | Honest about slow seconds | Names the bottleneck | Why it lost (or won) |
|---|---|---|---|
| One mean over the whole run | no | no | hides stalls; RT29 forbids it |
| Per-second distribution, one thread | yes | no | cannot tell generation from writing |
| Per-second distribution, two threads and bounded queue (this ADR) | yes | yes | won |
| Unbounded queue | yes | misleading | memory grows silently and hides the slow writer |
| `multiprocessing` writer | yes | yes | extra complexity before we know the thread layout is not enough |

## Consequences

- + The numbers answer RT29 and feed RT28 as measurement, never as projection.
- + The queue bound is testable (AC2) and keeps memory flat.
- − Python threads share the GIL; if the writer stage is the limit, the next step is a process, and
  that would be a new ADR.
- Revisit if two runs on one machine differ by more than the spread we accept (decided with the
  mentor after the first measured run).
