# Primer: acceptance criteria with EARS

## Why a sentence pattern

"The load should handle failures well" cannot be tested. A test needs a trigger, a system and an
observable response. **EARS** (Easy Approach to Requirements Syntax, Alistair Mavin et al.,
Rolls-Royce, 2009) gives a handful of sentence patterns that force exactly those parts, while
staying plain English. Kiro popularised it for AI coding; we use it in backlogs (acceptance
criteria) and specs (behaviours).

## The patterns

| Pattern | Template | Example from our domain |
|---|---|---|
| Ubiquitous | The `system` shall `response`. | The platform shall store every timestamp in UTC with its original offset. (RT12) |
| Event-driven | When `trigger`, the `system` shall `response`. | When a load completes, the loader shall record the requested and the received intervals. (RT03) |
| State-driven | While `state`, the `system` shall `response`. | While a reprocessing of a slice runs, the query API shall serve only the previous consistent version of that slice. (RT25) |
| Unwanted behaviour | If `condition`, then the `system` shall `response`. | If a record names an unknown tag, then the loader shall keep it pending with a reason and associate it with no asset. (RT10) |
| Optional feature | Where `feature is present`, the `system` shall `response`. | Where the source provides an update time, the loader shall store it separately from the occurrence and reception times. (RT07) |
| Complex | combinations, e.g. While …, when …, the … shall … | While the source is unavailable, when a retry fails for the third time, the loader shall stop and raise a visible alert. (RT05) |

## Rules of thumb

- **One "shall" per statement.** Two responses are two criteria.
- **Observable responses only.** "shall record", "shall reject", "shall return 422", not "shall be robust".
- **Numbers where it matters:** limits, times, percentiles (RT29 asks for p95, not just the mean).
- **Link each criterion to its RT** and, in the spec, give it an id (`SPEC-001-B03`) so tests and
  reviews can cite it.
- **Start from the RT's "how we verify it".** It is usually the test, already half-written.

## From criterion to test

```text
AC: If a record names an unknown tag, then the loader shall keep it pending with a reason
    and associate it with no asset.                                        (RT10)

test_unknown_tag_stays_pending_with_reason_and_no_asset():
    given a source record with tag "XYZ-999" that no mapping knows
    when the load runs
    then the record is in the pending list with reason "unknown tag"
    and no asset has a reading from "XYZ-999"
```
