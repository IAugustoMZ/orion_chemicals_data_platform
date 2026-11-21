# Validation · 001 · Time-series source: global time core

Reviewed the implementation shipped by PR #24 at merge commit `74bd96f`. The independent
review compared its first-parent diff with the approved specification and the test evidence.
G6 review is pending resolution of the blocking findings below.

## Verification (G5)

The dossier records a passing verification at `2026-11-15T18:16:54Z`, with base commit
`3f5f58b` and governed digest `938529e243f8`.

| Check | Recorded result |
| --- | --- |
| Format, lint, types | Passed. The run reported 319 formatted files and 93 type-checked source files. |
| Architecture | Passed. All six import contracts held. |
| Tests | Passed. Recorded in the dossier; the independent component rerun also passed 53 tests. |
| Security, secrets, dependencies | Passed. Recorded for Bandit, detect-secrets and the dependency audit. |
| Harness, docs site | Passed in the recorded build check. |

`sdd item merged 001 05` recorded commit `87efef9`. `sdd status 001` then reported G5 passed
on the same governed digest. The component rerun used Python 3.11.9 and tzdata 2026.6.
The documentation consistency check reported four warnings outside this dossier. A separate
strict site build aborted on two existing links in the dossier 003 teaching guide, to
`evidence/` and `compose.yaml`.

## Code review

| Severity | Location | Finding and proposed correction |
| --- | --- | --- |
| Blocking | [representation.py](../../src/tssource/domain/time/representation.py#L27) | The codec implements four conversions and returns bare UTC datetimes. Neither local form has a decode path and nothing builds `DecodedTimestamp` from an input. A caller cannot recover the source value or offset through the codec. Define the six-form contract and implement and test decoding that retains the input and metadata and delegates local resolution through the port. |
| Blocking | [representation.py](../../src/tssource/domain/time/representation.py#L54) | Numeric round trips discard fractional seconds or use floating-point arithmetic. A UTC instant with `.123457` seconds came back at `.000000` through epoch seconds, `.123000` through epoch milliseconds and `.123458` through FILETIME. Specify the representable precision of each form, use exact integer arithmetic for FILETIME and test fractional and pre-epoch inputs. |
| Blocking | [zoneinfo_resolver.py](../../src/tssource/infrastructure/zoneinfo_resolver.py#L39) | The first-valid search advances by one minute while retaining the starting seconds. Chicago `2024-03-10 02:15:30` returns `08:00:30Z`; the first valid instant is `08:00:00Z`. Resolve the true transition boundary and add a sub-minute regression case. |
| Blocking | [site_zone.py](../../src/tssource/domain/time/site_zone.py#L27) | The spec requires Shanghai and Kolkata to avoid gaps and ambiguity. The unrestricted IANA mapping gives the China site a gap on `1991-04-14`. Clarify the historical range or the fixed offset policy for the fictional sites and test its boundary. |
| Blocking | [app.py](../../src/tssource/interfaces/cli/app.py#L92) | The CLI accepts compact date `20240310` and a China request for `0001-01-01` exits 1 with a traceback. Enforce the documented date form and handle out-of-range UTC conversion as a usage error. |

The immutable event-time object retains the three UTC fields. The clock-fault probe confirmed
no change before activation, the configured offset at activation, and whole-day drift thereafter.
The changed source modules, classes and methods have explanatory docstrings.

## Architecture review

The source and test paths match the implementation plan. The domain imports standard-library
types and has no I/O. The application owns the resolver protocol and the 24-row iteration.
Bootstrap selects the declared site and wires the concrete adapter. The interface parses the date
and renders the returned rows. The benchmark path remains in place.

The timestamp value object exists, but the input-to-value path in the approved contract is missing.
The spec also counts five instant-bearing forms while naming two local forms without offsets.
Four forms currently carry enough information on their own. The contract needs a decision about
how ISO-local obtains the context needed for the fifth round trip.

## Security review

| STRIDE | Evidence and result |
| --- | --- |
| Spoofing | The CLI looks up `SiteCode` through a whitelist. An unknown site exited 2. |
| Tampering | The lock and the installed fallback both show tzdata 2026.6. The adapter uses the runtime's zone data provider; a Linux host can supply OS rules. The source-time metadata gap remains open under Code review. |
| Repudiation | The diff creates no mutable configuration or audit event. |
| Information disclosure | Ordinary invalid site and date return usage errors. The extreme-date CLI result disclosed a traceback. The recorded secret scan passed. |
| Denial of service | A request covers one date and one of five sites. The adapter bounds the search for a gap boundary to 1,440 probes per skipped value. |
| Elevation of privilege | The path performs local computation and reads installed zone rules through the standard library. It adds no external service, credentials, grants or writes. |

## Functional validation

| Behaviour or RT | How validated | Result |
| --- | --- | --- |
| B01 / RT12 | Site-zone tests plus the spring Chicago, Brussels and São Paulo CLI examples. Invoked the resolver directly for Chicago `02:15:30`. | Hour-aligned examples passed. The sub-minute gap returned a UTC instant 30 seconds after the boundary. |
| B02 / RT12 | Probed the repeated Chicago and Brussels hours and São Paulo's `2019-02-16 23:00` local hour. Compared India on `2024-03-10` with China on `1991-04-14`. | Both instants survived every repeated-time probe. India was ordinary on the sampled date. China returned a historical gap. |
| B03 / RT12 | Ran the four marked whole-second round trips and probed fraction `.123457`. Reviewed data flow into `DecodedTimestamp`. | Whole-second examples passed. Exact numeric round trips and original metadata retention are incomplete. |
| B04 / RT12 | Passed `2024-11-03T01:30:00` and `11/03/2024 01:30:00` to the local forms of the codec. | Both calls raised `ValueError`. The marked ambiguity test calls the resolver directly with an already parsed datetime. |
| B05 / RT07 | Constructed a synthetic corrected record with occurrence January 1, update February 1 and reception February 2, all UTC. Probed offset/drift on days −1, 0 and 2. | The three fields stayed separate. Clock adjustments were zero, five minutes, and seven minutes. This covers the value model; source-file preservation is outside card 05. |
| B06 | Called the installed `tssource time-table` entry point and exercised the Typer boundary with the test runner. | Ordinary valid dates yielded 24 rows plus a header. Invalid site and unparseable date exited 2. Compact date returned 0 and the earliest date example returned 1 with a traceback. |

## Documentation upkeep

- [x] ADR-0029 is accepted and linked from the decision index.
- [x] The architecture map explains the implemented path. The guide diagrams use the registered
  Python logo on the adapter node.
- [x] Root and component READMEs point readers to the implemented diagnostic.
- [x] The teaching guide describes the shipped implementation and the findings above.
- [ ] Close the implementation and contract findings and revalidate before requesting G6 approval.

## Build log

The task checklist and marked acceptance tests shipped with `87efef9`. After PR #24 merged,
the local feature ref was reconstructed at that verified commit so the SDD command could record
the merge. The independent component test run passed. The exploratory cases above found
specification gaps beyond the marked tests.

PBI-001-24 implements the revised G4 contract. Its marked tests cover exact numeric
conversion and original metadata, both offset-free forms, precise gap boundaries, historical
fixed offsets, and strict CLI date behavior. The card verification passed all ten quality
checks, including the strict documentation build. The independent review above describes PR #24.
The follow-up still needs independent validation before G6.

## Review notes (optional)

Keep G6 pending. Agree on the local timestamp and historical-zone contracts before modifying
the approved spec. The harness gives a merged card no transition back to build, so corrective
code needs an approved follow-up card.

The proposed contract uses the declared site for both offset-free forms. It requires an exact
round trip when the form can represent the input and retains the raw value in every decode.
It treats the fictional China and India sites as fixed UTC+08:00 and UTC+05:30, respectively,
while using civil zone rules for the other three sites.
