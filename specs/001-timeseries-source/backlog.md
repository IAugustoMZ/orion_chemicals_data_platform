# Backlog · 001 · Time-series source: global time core

> **Phase 2 · Plan**, closed by **G2 · Backlog approved** (both mentor and mentee approve).
> The prior umbrella backlog is intentionally replaced: [roadmap.md](roadmap.md) is the record of
> cards moved to other dossiers or already delivered by dossiers 002 and 003.

## Epics

| Epic | Outcome | PRD goal | RT coverage |
|---|---|---|---|
| E1 · Global time core | A deterministic, pure time library exposes realistic site-local time without silently guessing. | All three PRD goals | RT07, RT12 |

## Features

| Feature | User outcome | Item | Dependency |
|---|---|---|---|
| F1 · Civil-time semantics | An engineer can inspect UTC candidates, timestamp forms, three times, and clock faults for each fictional site. | PBI-001-05 | Dossier 003 merged |

## Order and dependencies

| Order | Item | Why now | Depends on |
|---|---|---|---|
| 1 | PBI-001-05 | Resolves the source-wide time risk before acquisition and writers reuse it. | Dossier 003 merged. |

## Work items

### PBI-001-05 · Time core: zones, daylight saving, representations, and wrong clocks

- **Feature:** F1 · Civil-time semantics
- **Serves:** RT07 and RT12.
- **Size:** L.
- **Depends on:** the merged `tssource` skeleton and CLI from dossier 003; existing `tzdata`.
- **Context:** Five fictional sites write civil time differently. A generator must create known
  answers for skipped and repeated local times before later acquisition and writers can use it.
  The source-side model keeps occurrence, source-update, and reception time separate; later
  dossiers apply it to streams and files. Tests use settled historical transitions, not future
  rules: Chicago 2024-03-10/11-03, Brussels 2024-03-31/10-27, and São Paulo 2018-11-04/
  2019-02-17. A gap remains visibly `gap` while resolving to its first valid instant after it.

#### What

Deliver a library and `tssource time-table --site <code> --date <YYYY-MM-DD>`. Sites are Brazil
(`America/Sao_Paulo`), US Gulf Coast (`America/Chicago`), Belgium (`Europe/Brussels`), China
(`Asia/Shanghai`), and India (`Asia/Kolkata`). Support ISO 8601 with offset, ISO local without
offset, epoch seconds, epoch milliseconds, local `MM/DD/YYYY HH:MM:SS`, and Windows FILETIME
ticks. Expose separate occurrence, source-update, and reception times; model constant-offset and
per-day-drift clock faults. Keep source values, their known zone/offset, and resolution explicit.

#### How

1. Add `src/tssource/domain/time/` modules `site_zone.py`, `resolution.py`,
   `representation.py`, `clock_fault.py`, and `event_times.py`. Use frozen value objects and
   UTC-aware `datetime`; the domain performs no I/O and imports no third-party library.
2. Define the application port `ZoneResolver` and `ResolveTimeTable` in
   `src/tssource/application/time_table.py`; add `ZoneInfoResolver` in
   `src/tssource/infrastructure/zoneinfo_resolver.py`. It uses `zoneinfo.ZoneInfo`, and detects
   valid/repeated/skipped civil time by `fold` candidates and UTC round-trip.
3. Wire the adapter in `src/tssource/bootstrap.py`; add the `time-table` Typer command in
   `src/tssource/interfaces/cli/app.py`. Validate site/date at the interface; invalid input exits
   2 with one safe line, never a traceback.
4. Add domain tests under `tests/tssource/domain/` and command tests in
   `tests/tssource/test_time_table.py`; every AC test carries its `@pytest.mark.ac` marker.

#### Out of scope

Generating event streams, writing source contracts or files, applying faults to a stream, leap
seconds, real plant access, and any new runtime dependency. Those concerns remain in the roadmap
dossiers.

#### Acceptance criteria (EARS)

- **AC1:** When a local time falls in the daylight-saving gap of a declared zone, then the resolver
  shall return `gap` and the first valid UTC instant after the gap.
- **AC2:** When a local time falls in the repeated hour of a declared zone, then the resolver shall
  return `ambiguous` and both UTC instants; China and India shall never return either state.
- **AC3:** When an instant is encoded in each of the six representations, then the five UTC or
  offset-bearing forms shall decode to the same instant while preserving their original value and
  known zone or offset.
- **AC4:** When local text without an offset is decoded, then the codec shall require its site zone
  and return an ambiguity result instead of selecting a fold.
- **AC5:** When `EventTimes` is created, then occurrence, source-update, and reception shall be
  separate UTC-aware values; while a clock fault is active, written occurrence time shall differ
  by exactly its configured offset or accumulated drift.
- **AC6:** When `tssource time-table --site CODE --date YYYY-MM-DD` runs, then it shall print each
  requested local time, UTC candidate(s), offset(s), and resolution; invalid input shall exit 2.

#### Verification

| Criterion | Marked test | Fixed evidence |
|---|---|---|
| AC1 | `tests/tssource/domain/test_site_zone.py::test_gap_returns_first_valid_instant` | Chicago 2024-03-10 and Brussels 2024-03-31. |
| AC2 | `tests/tssource/domain/test_site_zone.py::test_repeated_time_returns_both_instants` | Chicago 2024-11-03, Brussels 2024-10-27, Shanghai/Kolkata fixed offsets. |
| AC3 | `tests/tssource/domain/test_representation.py::test_utc_forms_round_trip` | Six declared forms and one fixed UTC instant. |
| AC4 | `tests/tssource/domain/test_representation.py::test_local_text_keeps_ambiguity` | Chicago repeated hour. |
| AC5 | `tests/tssource/domain/test_event_times.py`, `test_clock_fault.py` | Fixed UTC instants; offset and drift boundaries. |
| AC6 | `tests/tssource/test_time_table.py` | Valid output and invalid site/date exit code. |

Every listed test shall use the matching marker `@pytest.mark.ac("PBI-001-05:ACn")`; the card
also passes `poetry run sdd item verify 001 05` before its pull request is opened.

## Definition of done

PBI-001-05 is done only when both members approved its current text, every marked acceptance test
passes, `poetry run sdd item verify 001 05` passes, its branch is committed and pushed, and its
pull request is open for a person to merge.
