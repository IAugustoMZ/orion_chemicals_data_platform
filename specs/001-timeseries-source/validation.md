# Validation · 001 · Time-series source: global time core

The original review covered PR #24 at merge commit `74bd96f`. PR #26 at merge commit
`909604e` implements the revised specification. PR #27 at merge commit `7f1c488` closes the
ISO-offset finding from PR #26. The original findings are retained below alongside the
evidence for their corrections.

## Verification (G5)

The dossier records a passing verification at `2026-11-23T01:58:34Z` for merge commit
`7f1c488` and governed digest `a03b3de7fc0a`.

| Check | Recorded result |
| --- | --- |
| Format, lint, types | Passed. The run reported 322 formatted files and 94 type-checked source files. |
| Architecture | Passed. All six import contracts held. |
| Tests | Passed. 333 tests and 95.77% coverage. |
| Security, secrets, dependencies | Bandit, detect-secrets and the dependency audit passed. |
| Harness, docs site | The harness consistency check and strict MkDocs build passed. |

The card ledger records cards 05, 24 and 25 as merged at commits `87efef9`, `6c59112`
and `5fe0a4e`, respectively. `sdd status 001` reports G5 passed on the merged code.

## Code review

The following findings came from the original PR #24 review.

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

The independent PR #26 review confirmed that the prior five findings are addressed for the
specified cases. It found a remaining blocker in the direct ISO-offset input path.

| Severity | Location | Finding and proposed correction |
| --- | --- | --- |
| Blocking | [representation.py](../../src/tssource/domain/time/representation.py#L79) | The decoder accepts `2024-01-01T00:00:00+00:60` and treats it as `+01:00`, moving the decoded instant by an hour. It accepts `2024-01-01T00:00:00+00:00.5` and drops the nonzero offset fraction. Validate the supported offset-bearing syntax and component ranges before parsing. Test exact accepted forms and rejection of malformed or unsupported spellings. |

The independent PR #27 review confirmed that the ISO parser checks offset component
ranges and requires explicit seconds before accepting a fraction. It checks both fractions
against datetime precision and adjusts the parsed zone when Python discards a fractional
offset with zero whole seconds. The assembled codec rejects both original reproducers and
retains the raw value, format and normalized offset on valid inputs. No blocking finding
remains in the reviewed scope.

## Architecture review

The source and test paths match the implementation plan. The domain imports standard-library
types and has no I/O. The application owns the resolver protocol and the 24-row iteration.
Bootstrap selects the declared site and wires the concrete adapter. The interface parses the date
and renders the returned rows. The benchmark path remains in place.

PR #26 connects the input path to `DecodedTimestamp`. The application delegates direct formats
to the domain and uses the `ZoneResolver` port for both local formats. Bootstrap wires the
adapter. PR #27 applies the ISO-offset correction at the existing domain parser boundary.
The diff adds no dependency, I/O path or layer crossing.

## Security review

| STRIDE | Evidence and result |
| --- | --- |
| Spoofing | The CLI looks up `SiteCode` through a whitelist. An unknown site exited 2. |
| Tampering | QA confirmed metadata retention and exact results for the standard fixtures. On PR #27 the original malformed ISO-offset cases raise a value error, and accepted offsets yield the expected UTC instant. The adapter uses the runtime's zone data provider, which can be supplied by the host. |
| Repudiation | The diff creates no mutable configuration or audit event. |
| Information disclosure | Six representative invalid inputs, including range boundaries, exited 2 with one diagnostic, empty stdout and no traceback. The secret scan passed. |
| Denial of service | A request covers one date and one of five sites. The adapter bisects the interval between the gap's two UTC probes down to datetime precision. |
| Elevation of privilege | The path performs local computation and reads installed zone rules through the standard library. It adds no external service, credentials, grants or writes. |

## Functional validation

The table below records the original PR #24 probes and their outcomes.

| Behaviour or RT | How validated | Result |
| --- | --- | --- |
| B01 / RT12 | Site-zone tests plus the spring Chicago, Brussels and São Paulo CLI examples. Invoked the resolver directly for Chicago `02:15:30`. | Hour-aligned examples passed. The sub-minute gap returned a UTC instant 30 seconds after the boundary. |
| B02 / RT12 | Probed the repeated Chicago and Brussels hours and São Paulo's `2019-02-16 23:00` local hour. Compared India on `2024-03-10` with China on `1991-04-14`. | Both instants survived every repeated-time probe. India was ordinary on the sampled date. China returned a historical gap. |
| B03 / RT12 | Ran the four marked whole-second round trips and probed fraction `.123457`. Reviewed data flow into `DecodedTimestamp`. | Whole-second examples passed. Exact numeric round trips and original metadata retention are incomplete. |
| B04 / RT12 | Passed `2024-11-03T01:30:00` and `11/03/2024 01:30:00` to the local forms of the codec. | Both calls raised `ValueError`. The marked ambiguity test calls the resolver directly with an already parsed datetime. |
| B05 / RT07 | Constructed a synthetic corrected record with occurrence January 1, update February 1 and reception February 2, all UTC. Probed offset/drift on days −1, 0 and 2. | The three fields stayed separate. Clock adjustments were zero, five minutes, and seven minutes. This covers the value model; source-file preservation is outside card 05. |
| B06 | Called the installed `tssource time-table` entry point and exercised the Typer boundary with the test runner. | Ordinary valid dates yielded 24 rows plus a header. Invalid site and unparseable date exited 2. Compact date returned 0 and the earliest date example returned 1 with a traceback. |

A separate QA session ran `poetry run pytest -q --no-cov tests/tssource` after PR #26 merged.
All 83 component tests passed. Synthetic exploratory checks gave these results.

| Behaviour or RT | Probe and result |
| --- | --- |
| B01 / RT12 | Sub-minute gap inputs in Chicago, Brussels and São Paulo resolved to the first valid instant: `08:00Z`, `01:00Z` and `03:00Z`, respectively. |
| B02 / RT12 | Historical China and India inputs resolved uniquely at `+08:00` and `+05:30`. |
| B03 / RT12 | Standard direct-form samples retained their original data and exact instant. Malformed and shortened ISO offsets reproduced the blocking finding above. |
| B04 / RT12 | Both forms encoded the two Chicago UTC candidates to the same wall value and decoded it to `06:30Z` and `07:30Z` in order. |
| B05 / RT07 | The three synthetic event times stayed separate. Clock adjustments at days −1, 0 and 2 were zero, five and seven minutes. |
| B06 / RT12 | Each site's installed CLI run produced 25 lines and repeated byte for byte. Six invalid inputs exited 2 with a single diagnostic, empty stdout and no traceback. |

Independent validation on the PR #27 merge used the assembled codec and installed CLI.

| Behaviour or RT | Result |
| --- | --- |
| B01–B02 / RT12 | Sub-minute gaps in Chicago, Brussels and São Paulo resolved to the exact UTC boundary and preserved the requested wall reading. Historical China and India probes returned a single candidate under their declared fixed offsets. |
| B03 / RT12 | Seven malformed or over-precise offsets and two UTC range overflows raised `ValueError`. Six accepted examples retained their original value, form and offset, with exact UTC results. These included compact and colon-delimited offsets, both signs of a half-second offset and a near-24-hour offset. Negative epoch seconds and milliseconds and one exact FILETIME sample retained their original metadata. Inexact numeric values raised `ValueError`. |
| B04 / RT12 | Both local forms required a site. Each encoded the two Chicago UTC candidates to the same local text, and decoding returned both candidates in UTC order with the original text and zone. |
| B05 / RT07 | A corrected synthetic event retained occurrence, source update and reception as three distinct UTC values. The clock fault left the instant before activation intact, applied five minutes at activation and seven minutes after two days. |
| B06 / RT12 | The installed CLI returned a header and 24 rows for each of the five sites, with byte-for-byte repeatability. Five invalid inputs covering site, date syntax, calendar date and both UTC range boundaries exited 2 with one error, empty stdout and no traceback. |

## Documentation upkeep

- [x] ADR-0029 and ADR-0030 are accepted and linked from the decision index.
- [x] The architecture map explains the implemented path. The guide diagrams use the registered
  Python logo on the adapter node.
- [x] Root and component READMEs point readers to the implemented diagnostic.
- [x] The teaching guide describes the shipped implementation and the findings above.
- [x] Close the ISO-offset blocker and rerun independent validation on merged code.

## Build log

The task checklist and marked acceptance tests shipped with `87efef9`. After PR #24 merged,
the local feature ref was reconstructed at that verified commit so the SDD command could record
the merge. The independent component test run passed. The exploratory cases above found
specification gaps beyond the marked tests.

PBI-001-24 implements the revised G4 contract. Its marked tests cover exact numeric
conversion and original metadata, both offset-free forms, precise gap boundaries, historical
fixed offsets, and strict CLI date behavior. The card verification passed all ten quality
checks, including the strict documentation build. The independent review and QA of PR #26
closed the original issues and found the remaining ISO-offset parsing defect.

PBI-001-25 validates ISO offset components before the standard-library conversion. The new
tests reproduced nine failures on the prior parser. `poetry run sdd item verify 001 25` passed
both acceptance criteria and all ten quality checks after the correction.

After PR #27 merged, `sdd item merged 001 25` recorded the merge and `sdd verify 001` passed all
ten checks on the merge commit.

## Review notes (optional)

PBI-001-25 closes the ISO-offset finding under the existing B03 exactness contract. The
independent follow-up also rechecked B01–B06 against the merged code.
