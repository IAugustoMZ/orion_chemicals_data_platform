# PRD · 001 · Time-series source: global time core

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/001-timeseries-source/` · branch `spec/001-timeseries-source` · kind **feature** · created 2026-11-04.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

> **Re-scope (2026-11-13).** The first version of this PRD covered the whole generator. A
> specification is one file of at most 50 lines, so the need was split into nine dossiers (see
> [roadmap.md](roadmap.md)). This dossier keeps the first of them: the **global time core**. The
> PRD of the first version is in `main` at commit `42547d0`.

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT07 | P | When available, the occurrence time, the update time at the source and the reception time shall be stored separately. | Receive today an old record that was corrected; verify the three timestamps. |
| RT12 | P | Interpretable timestamps shall be standardised in UTC, preserving the original representation and time zone/offset when known; ambiguities shall be flagged. | Test two time zones and one record with an ambiguous time. |

**What this means in plain words.** The platform cannot prove it handles time until something
produces timestamps the way five plants in five countries really write them: different zones,
daylight saving rules that change on different dates, text without an offset, and clocks that are
simply wrong. This work is the **time core of that producer**: a small library with a command that
shows how a local time becomes UTC, plus the three timestamps of one event. It does not generate
events or write files (the dossiers listed in the roadmap do); it makes sure that every one of
them gets time right, because a wrong rule would poison every later test. It serves RT12 (UTC,
original representation kept, ambiguity flagged) and RT07 (occurrence, source update and reception
time kept apart) on the producer's side only: how the platform stores them is the ingestion
feature.

**Related RTs left out, and why.**
- RT23 (late data placed in its occurrence period): needs events, outages and a pipeline. It is
  served by the acquisition dossier, which reuses this time core.
- RT02, RT09, RT17, RT28, RT29, RT38, RT39, RT40: served by the other dossiers of the
  [roadmap](roadmap.md); none needs the time core alone.
- RT08, RT10, RT13, RT14, RT18, RT22 and RT30: about how the platform treats the data, as in the
  first version of this PRD.

**RTs this work must not break.** RT01 (read-only) and RT36 (no credentials in code, compose
files or output): the library reads no system and holds no secret.

## Problem

Orion Chemicals is the fictional company this repository builds a data platform for; its plants in
five countries are simulated, like everything else here. The team that builds the platform (the
mentor and the mentee) has no plant to connect to, and a platform tested on tidy toy data fails
on the first realistic file. For time, the concrete questions are: what does the platform do when a
US Gulf Coast server stores local time without an offset and the clocks change at night, so one
hour exists twice and another never exists? When a site's clock is set to local time but labelled
UTC, or drifts a few seconds a day? When the same instant arrives as ISO text, epoch seconds,
epoch milliseconds, a US-style date text or a Windows tick count? When an old reading is corrected
later, so that the time it happened, the time the source stored it and the time we received it all
differ?

Without a source that produces these cases, on purpose and with a known true answer, those
questions are answered by luck on real data later, and a wrong daylight saving rule in the
generator would make every other test lie.

## Goals and success metrics

Targets are our starting point; none depends on a measurement.

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| Daylight saving and zones behave exactly like the real rules | listed transitions of the five sites (US spring and autumn, EU spring and autumn, Brazil with and without daylight saving, China and India with a fixed offset) reported correctly as `ok`, `gap` or `ambiguous` | none | 100% of the listed transitions, each with its date written in the test and the time zone database version named | table-driven tests over the transitions; `tssource time-table` run for a gap, an ambiguous hour and a fixed-offset site |
| The same instant can be written in every representation the sites use, and read back safely | representations (ISO with offset, ISO local, epoch seconds, epoch milliseconds, local text, FILETIME ticks) that encode and decode; share of the ambiguous local times that are flagged instead of chosen silently | none | 6 of 6 encode; the 5 that carry an offset or are UTC decode to the same instant; 100% of the ambiguous local times flagged | round-trip tests per representation; test of the ambiguous hour on a local text |
| Three timestamps per event and clocks that can be wrong on purpose | events carrying occurrence, source update and reception time, all UTC; clock faults (constant offset, drift per day) that move the written time by exactly the declared amount | none | 100% of events built with the three times; the written occurrence time differs from the true instant by the declared offset or accumulated drift, and by nothing else | tests of the event-times value object and of the clock fault |

## Users and scenarios

- **Data engineer (the mentee, then the team), building ingestion.** Asks "what is 02:30 on
  2026-11-01 in the Gulf Coast plant?" and gets two UTC instants and the word `ambiguous`; then
  asks the same for a Chinese plant and gets one instant and `ok`. The scenario that matters: the
  engineer feeds the platform a local text taken from this library and checks that it refuses to
  guess (RT12).
- **The later dossiers (acquisition, source contract, final trial).** Call the library to stamp
  every event with its three times and to write them in the representation the site's contract
  declares. They need it to be pure, deterministic and tested before they are built.
- **The mentor, teaching.** Shows in a session why daylight saving gaps and repeated hours break
  naive code, using the command and the tests as the examples.

## Scope

### In scope

- A **time library** inside the `tssource` package: the zone of each of the five fictional sites
  (Brazil `America/Sao_Paulo`, US Gulf Coast `America/Chicago`, Belgium `Europe/Brussels`, China
  `Asia/Shanghai`, India `Asia/Kolkata`), a resolver of local time to UTC that reports `ok`, `gap`
  or `ambiguous`, six timestamp representations with encode and decode, the three timestamps of an
  event (RT07) and clock faults (constant offset or drift per day).
- A **command** `tssource time-table --site <code> --date <YYYY-MM-DD>` that prints, for local
  times of that date, the UTC instant(s), the offset and the flag.
- Tests with the real transitions of the years we choose, the date written in each test.

### Out of scope

- Generating events, signals or faults, and writing files: other dossiers of the roadmap.
- Applying a clock fault to a stream and late data after an outage (acquisition dossier).
- Leap seconds.
- Any real system or real data: none exists here, and everything is fictional.
- How the platform stores or reads the timestamps: the ingestion feature.

## Constraints and assumptions

- Local only: the library runs inside the existing `tssource` package and container
  (dossier 003); no cloud, no new service. Python through Poetry only; everything in English.
- Decision (mentor, 2026-11-04): Orion Chemicals, its five sites and all their data are
  fictional. The sites are chosen because their time rules differ; the zones and daylight saving
  rules are real-world rules applied to invented plants.
- Decision (mentor, 2026-11-13): a specification is one file of at most 50 lines; the need was
  split into the dossiers of the roadmap. This dossier keeps one card.
- Decision (mentor, 2026-11-04): the backlog is approved one card at a time (`sdd item`).
- Assumption: the standard library `zoneinfo` with the `tzdata` package (already a dependency of
  the `tssource` group) gives the real rules; we name the database version in the tests.
- Assumption: the offsets of China (+08:00) and India (+05:30) never change in the years we test.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| A daylight saving or zone rule is reproduced wrongly | the platform is tested against a false reality | rules come from the time zone database, never typed by hand; every transition has its date in a test (owner: mentee) |
| The time zone database changes in a later release (for example Brazil in 2019) | a test that passed starts failing, or an old date is read with a new rule | name the database version in the tests and the ADR; tests use fixed dates (owner: mentee) |
| Windows FILETIME ticks (100 ns since 1601) lose precision in floating point | an instant is off by microseconds | use integers; test the round trip at the edges (owner: mentee) |
| Open question: should a gap time return the next valid instant or an error? | the later dossiers behave differently | proposed: report `gap` and return the next valid instant, as the first backlog says; confirm at the specification (owner: mentor) |
| The roadmap changes while we learn | cards move between dossiers again | the roadmap is amended in the open and each dossier is re-approved only for what changed (owner: mentor) |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
