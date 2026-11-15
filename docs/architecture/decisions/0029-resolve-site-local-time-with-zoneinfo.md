# ADR-0029: We resolve site-local time with zoneinfo and explicit civil-time outcomes

- **Status:** Accepted
- **Date:** 2026-11-13
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT07, RT12; refines [ADR-0019](0019-tssource-package-and-dependencies.md) and [ADR-0022](0022-hidden-plant-and-site-local-time.md)

## Context

The synthetic source writes time as five sites would: civil times in zones with changing rules,
fixed offsets, ambiguous repeated hours, and skipped hours. RT12 requires UTC normalisation while
retaining the original representation and known offset, and prohibits silently guessing an
ambiguous time. RT07 also needs three separately modelled times. Python already supplies
`zoneinfo`; the existing `tzdata` dependency makes its data available in the pinned slim image.

## Decision

We use `zoneinfo.ZoneInfo` through an infrastructure adapter. The domain receives a
`LocalResolution`: `ok` with one UTC candidate, `ambiguous` with both candidates, or `gap` with
the first valid instant after the gap. Local text decoding requires a site zone and returns that
resolution; it never selects a fold. Internal event times are UTC-aware and separate occurrence,
source-update, and reception values.

## Alternatives considered

| Option | RT12 ambiguity | Dependency cost | Why it lost or won |
|---|---|---|---|
| Attach a zone and accept the default fold | Fails | None | Silently guesses a repeated local time. |
| Reject every gap and ambiguity | Preserves ambiguity | None | Makes realistic generated cases unusable without a declared gap policy. |
| Pendulum/dateutil | Can work | New runtime dependency | Duplicates standard-library capability. |
| `zoneinfo` with explicit outcomes | Meets | Existing Python and `tzdata` | Won. |

## Consequences

- The source can generate and expose DST edge cases with a known answer.
- Consumers must handle an explicit unresolved local value, which is intentional RT12 exercise.
- TZDB updates can change historical rules; fixed-date tests and the locked `tzdata` version make that visible.
- Revisit if a future external source supplies a timestamp representation not covered by the six declared forms.
