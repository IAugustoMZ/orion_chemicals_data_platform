# Implementation plan · 001 · Time-series source: global time core

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. The plan says *how* the build will proceed; the spec says *what* it must achieve.

## Approach

Build pure domain contracts and transition tests first, isolate `zoneinfo` behind a port, add codecs
and clock rules, then expose the thin `time-table` command. Each task is small enough for its own
approved card branch and starts with acceptance tests.

## Steps

1. Define site, resolution, and error value objects; table-test the five zone policies and DST cases. *(B01, B02)*
2. Add the `ZoneResolver` port and `ZoneInfoResolver`; prove gap/repeated detection by UTC round-trip. *(B01, B02)*
3. Add timestamp representations and decoded-value contracts; test exact and unresolved round trips. *(B03, B04)*
4. Add `ClockFault` and `EventTimes`; test UTC invariants and fault boundaries. *(B05)*
5. Wire `ResolveTimeTable` in `bootstrap.py`; add the Typer command and CLI integration tests. *(B06)*
6. Update component/architecture documentation, run `sdd verify 001`, and record G5 evidence. *(All)*

## Files to create or change

| Area | Files |
|---|---|
| Domain | `src/tssource/domain/time/{__init__,site_zone,resolution,representation,clock_fault,event_times}.py`; `domain/errors.py` if typed time errors are needed. |
| Application | `src/tssource/application/time_table.py`. |
| Infrastructure | `src/tssource/infrastructure/zoneinfo_resolver.py`. |
| Interface/root | `src/tssource/bootstrap.py`, `src/tssource/interfaces/cli/app.py`. |
| Tests | `tests/tssource/domain/test_{site_zone,representation,clock_fault,event_times}.py`, `tests/tssource/test_time_table.py`, fakes only if a port needs one. |
| Documents | `src/tssource/README.md`, `docs/architecture/README.md`, ADR-0029, teaching guide at G6. |

## Rollback

Revert the individual merged card commit. This work has no persistent output or external write;
the TZDB dependency already exists, so no data cleanup or dependency removal is necessary.

## Risks during the build

| Risk | Early signal | Response |
|---|---|---|
| Incorrect gap/repeated classification | Transition-table test disagrees with expected UTC candidates. | Stop the card; compare the `fold` round-trip rule with ADR-0029 before changing code. |
| Host/container TZDB differences | The same test differs locally and in the pinned image. | Pin/assert the `tzdata` version and investigate before approval. |
| Ambiguous local text gets coerced | Codec test produces one instant for a repeated hour. | Keep `LocalResolution` in the API; do not add a default fold. |
| Scope expands into event generation | A proposed file touches stream writers or acquisition. | Stop and open the relevant roadmap dossier instead. |
