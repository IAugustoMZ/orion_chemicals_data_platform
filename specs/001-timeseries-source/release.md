# Release and learnings · 001 · Time-series source: global time core

> **Phase 7 · Release & Learn**, closed by **G7 · Results validated** (both of us approve).
> How to fill this file: [lifecycle, phase 7](../../harness/lifecycle.md#phase-7-release-and-learn).

## Release

| Item | Evidence |
|---|---|
| Merged work | PR #27 at `7f1c488` contains the final ISO-offset fix. PR #28 at `9373e9b` records G6. The image was built from `9373e9b`. |
| Local service | Docker Compose `tssource` was healthy on 2026-11-23 UTC. Image `orion/tssource:local`, ID `sha256:4763288e404460144eff855e03af1f8811d662a246df987f80aa61e4e0a6a7e0`. |
| Data migration | None. The time core uses in-memory values and prints diagnostic output. |

```bash
docker compose build tssource
docker compose up -d --no-build --wait --wait-timeout 60 tssource
docker compose ps tssource
docker compose exec -T tssource tssource health
docker compose exec -T tssource tssource time-table --site us-gulf-coast --date 2024-11-03
```

## Observation

The Compose health check passed and the direct health command exited 0. The idle service
emitted no logs during the check. Container probes exercised the installed CLI and assembled
codec. The system time-zone database and the installed `tzdata` 2026.6 wheel both reported
IANA version 2026f.

| Probe | Observed result |
|---|---|
| Site policy | Three sub-minute gaps returned the first valid UTC instant and preserved the requested wall time. Three repeated hours returned both UTC candidates in order. Two historical fixed-offset probes returned one candidate each. |
| Timestamp codec | All six forms round-tripped an exact instant and retained the raw value and source reference. Malformed offsets, excess offset precision, an inexact FILETIME input and an inexact epoch-millisecond encoding raised `ValueError`. Both signed half-second offsets converted exactly. Both local forms returned both candidates for the repeated Chicago hour. |
| Event clock | A corrected synthetic event kept distinct UTC values for occurrence, source update and reception. A constant offset added five minutes. With drift configured, the shift was zero before activation, five minutes at activation and seven minutes after two days. |
| Installed CLI | All five site tables produced 24 rows plus a header and repeated byte for byte. The unknown site and both UTC range failures exited 2 with one diagnostic, empty stdout and no traceback. |

The installed CLI printed these rows for the US Gulf Coast site. On November 3, 2024,
`01:00` occurred twice. On March 10, 2024, `02:00` was skipped and the command reported
the first valid UTC instant after the gap.

```text
local | resolution | offsets | utc candidates
01:00 | ambiguous | -1 day, 19:00:00, -1 day, 18:00:00 | 2024-11-03T06:00:00Z, 2024-11-03T07:00:00Z
02:00 | gap | -1 day, 19:00:00 | 2024-03-10T08:00:00Z
03:00 | ok | -1 day, 19:00:00 | 2024-03-10T08:00:00Z
```

## Feedback

The G6 review was approved by both reviewers. Product feedback from using the released
container is pending the G7 review. During closeout, the maintainer asked the harness to
document that agents can open pull requests with the installed GitHub CLI.

## Results against the goals

| PRD goal | Result | Evidence |
|---|---|---|
| Daylight saving and offsets follow each fictional site's declared policy | Met | The container returned the expected UTC candidates or gap boundary in all eight site-policy probes. |
| Every declared timestamp format can be written and read without silently losing meaning | Met | The container passed the six-form round trip, metadata, precision rejection and repeated-hour probes. [G5 and functional validation](validation.md) cover additional exactness and range cases. |
| Three timestamps per event and clocks that can be wrong on purpose | Met for the time core | The corrected-event and clock-fault probes passed. The in-scope evidence is the event value object and clock-fault function. Stream generation and ingestion are later work. |

## Learnings

- A local reading in a repeated hour can map to two physical instants. Consumers need source
  evidence to choose one and can preserve both candidates until that evidence is available.
- The container exposes the time-zone database version for reproducing transition checks.
  The exactness probes catch silent changes that a whole-second round trip can miss.
- GitHub CLI 2.104.0 was available and successfully opened the closeout PR. The proposed
  harness guidance is to use `gh pr create --base main --head <branch>` when delivering
  an authorised change, then hand the PR to a person for merge.

## Next items

- Open Plant and tag catalogue next on the [time-series roadmap](roadmap.md).
- Track the GitHub CLI guidance in a harness enabler, with scope limited to opening and
  handing off pull requests.
