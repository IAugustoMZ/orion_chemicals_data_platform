# ADR-0019: The generator is a second clean-architecture package with its own dependency group

- **Status:** Proposed
- **Date:** 2026-11-12
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT28, RT29, RT01, RT36; refines [ADR-0005](0005-poetry-for-every-python-environment.md) and [ADR-0007](0007-clean-architecture-for-all-python-code.md)

## Context

Dossier 001 adds the first platform component: a generator of plant time-series. It needs numeric
arrays at tens of thousands of events per second, a columnar file format and time zone data,
none of which the harness (`tools/sdd`) uses. Principle 7 says new dependencies enter only
through a spec that names them, and each deployable gets its own Poetry group.

## Decision

We create the package `tssource` under `src/tssource/` with the four layers of
[principles](../../../harness/principles.md) and one composition root. Its dependencies live in a
Poetry group `tssource`: `numpy`, `pyarrow` and `tzdata`. `typer` and `pyyaml` are reused. The
import-linter contracts of `sdd` are copied for `tssource`, and `domain` and `application` may not
import `numpy`, `pyarrow` or `typer`. The domain stays free of libraries; vectorised generators live
in `infrastructure` behind ports.

## Alternatives considered

| Option | Speed | Purity of the domain | Why it lost (or won) |
|---|---|---|---|
| Pure Python in the domain | slow | perfect | cannot reach 25,000 events/s with 2,050 tags |
| numpy inside the domain | fast | broken | the domain would depend on a library; layers would blur |
| numpy in infrastructure behind ports (this ADR) | fast | kept | won |
| Polars or pandas | fast | broken | heavier, no gain over numpy for random walks and arrays |

## Consequences

- + The domain stays testable without numpy; the fast paths are replaceable adapters.
- + The image installs only the group it needs.
- − Some rules (the swinging door) need a numpy-free reference implementation beside the fast one;
  both are tested against each other.
- Revisit if the spike (card 04) shows that array types must cross the application boundary.
