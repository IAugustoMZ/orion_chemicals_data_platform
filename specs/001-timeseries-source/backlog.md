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
| F1 · Civil-time semantics | An engineer can inspect UTC candidates, timestamp forms, three times, and clock faults for each fictional site. | PBI-001-05, PBI-001-24 | Dossier 003 merged |

## Order and dependencies

| Order | Item | Why now | Depends on |
|---|---|---|---|
| 1 | PBI-001-05 | Resolves the source-wide time risk before acquisition and writers reuse it. | Dossier 003 merged. |
| 2 | PBI-001-24 | Closes the RT12 findings from validation before other dossiers rely on the timestamp contract. | PBI-001-05 merged. |

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

### PBI-001-24 · Complete timestamp conversions and site-time resolution

- **Feature:** F1 · Civil-time semantics.
- **Serves:** RT12. RT07 is covered by PBI-001-05.
- **Size:** M.
- **Depends on:** PBI-001-05 merged in PR #24.
- **Context:** [Validation](validation.md#functional-validation) found that offset-free inputs
  cannot be decoded, source metadata and precision can be lost, and the CLI can accept compact
  dates or fail with a traceback. The fictional sites' declared rules also differ from their
  current historical behavior.

#### What

Complete the six-form timestamp codec with exact conversions at each format's supported precision.
Expose the original input, its `TimestampForm`, the known zone or offset, and the UTC resolution.
Require a declared site for `ISO_LOCAL` and `LOCAL_TEXT`. Resolve using civil rules for Brazil,
the US Gulf Coast and Belgium and fixed offsets for China and India. Both UTC instants in a
repeated hour can be encoded in either local form. Decoding that local value reports both UTC
candidates. Enforce the documented `time-table` date syntax and return a usage error for a date
that cannot produce a complete UTC table.

#### How

1. Extend `src/tssource/domain/time/representation.py` around `TimestampForm` and
   `DecodedTimestamp`. Preserve existing exact `encode_instant` and `decode_instant` calls for
   the four forms that resolve directly. Use integer arithmetic for epoch units and FILETIME.
   Apply the selected form's precision explicitly, including for instants before the Unix epoch.
2. Orchestrate the local codec path in the application using the existing `ZoneResolver` port
   in `src/tssource/application/time_table.py`. Parse and render local text with the existing
   domain forms. Use the declared site's rules for both UTC-to-local encoding and local-to-UTC
   decoding. Keep `ZoneInfo` in infrastructure and reuse `LocalResolution` for both paths.
3. Represent the fixed offsets on the declared sites in `src/tssource/domain/time/site_zone.py`.
   In `src/tssource/infrastructure/zoneinfo_resolver.py`, use those offsets directly and locate
   the boundary of a skipped interval with a bounded search at datetime precision.
4. Validate the date shape in `src/tssource/interfaces/cli/app.py` before parsing. Route UTC
   range errors through the existing Typer usage error path before writing table output.

#### Out of scope

Event stream generation, changes to the three event-time fields or clock faults, leap seconds,
new dependencies, and ingestion storage. The roadmap covers acquisition and source writers.

#### Acceptance criteria (EARS)

- AC1: When a directly resolved timestamp is decoded, the codec shall return its UTC instant,
  original value, form, and offset when known, with exact round trips for representable inputs.
- AC2: If an instant cannot be represented exactly at the chosen format's precision or within its
  range, then the encoder shall return an error.
- AC3: When either offset-free form is encoded or decoded, the codec shall use the declared site
  and return its local representation on encode or its original value, form, site zone or offset,
  and explicit `ok`, `gap`, or `ambiguous` resolution on decode. For a repeated hour, encoding
  either UTC instant yields the same local value and decoding it yields both UTC candidates.
- AC4: When a requested local reading falls in a gap, the resolver shall preserve that reading
  and return `gap` with the first valid UTC instant after the gap and that instant's offset.
- AC5: When a supported local reading is resolved at China or India, the resolver shall return one
  `ok` candidate with UTC+08:00 or UTC+05:30 respectively, including on historical dates.
  A decoded local timestamp retains the original input and the applicable declared offset.
- AC6: If the date is invalid, differs from `YYYY-MM-DD`, or produces an out-of-range UTC value,
  then `time-table` shall exit `2` with a single short usage error and without a traceback or
  partial table.

#### Verification

| Criterion | Test path | Fixed evidence |
|---|---|---|
| AC1 | `tests/tssource/domain/test_representation.py` | ISO text with `+05:30` and microseconds, epoch seconds and milliseconds on both sides of 1970, and a FILETIME round trip at `.123457`. |
| AC2 | `tests/tssource/domain/test_representation.py` | A subsecond instant in epoch seconds and local text, a submillisecond instant in epoch milliseconds, and an instant before the FILETIME epoch. |
| AC3 | `tests/tssource/` | Both local forms at ordinary, repeated, and skipped Chicago readings. Encode both UTC instants for `2024-11-03 01:30` and assert equal output, raw value retention, and both decoded UTC candidates. Exercise missing-site errors. |
| AC4 | `tests/tssource/domain/test_site_zone.py` | Chicago `2024-03-10 02:15:30.123456` resolves to `08:00:00Z` with offset `-05:00`. |
| AC5 | `tests/tssource/` | China on `1991-04-14`, India on `1942-09-01`, and a modern date at both sites. Check the preserved text and declared offset on decode for both local forms and sites. |
| AC6 | `tests/tssource/test_time_table.py` | `20240310`, an invalid calendar date, and China on `0001-01-01` exit `2`. Assert one usage error and no table output. A valid date still produces 24 rows. |

Use the corresponding `@pytest.mark.ac("PBI-001-24:ACn")` marker for each case. The card passes
`poetry run sdd item verify 001 24` before its pull request is opened.

## Definition of done

Each card is done only when both members approved its current text, every marked acceptance test
passes, `poetry run sdd item verify` passes for the card, its branch is committed and pushed, and
its pull request is open for a person to merge.
