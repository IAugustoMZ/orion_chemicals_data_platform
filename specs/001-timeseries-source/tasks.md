# Tasks · 001 · Time-series source: global time core

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. During the build, tick the boxes: ticking does not invalidate G4, but rewording, adding or removing a task does.

## Tasks

- [x] T01 · Add failing site-zone and local-resolution transition tests, then implement the pure domain values. *(SPEC-001-B01, B02; plan step 1)*
- [x] T02 · Add the zone-resolver port and `zoneinfo` adapter; make the DST tests pass. *(SPEC-001-B01, B02; plan step 2)*
- [x] T03 · Add failing codec tests, then implement the six representations and explicit local-text decoding. *(SPEC-001-B03, B04; plan step 3)*
- [x] T04 · Add failing three-time and clock-fault tests, then implement their value objects. *(SPEC-001-B05; plan step 4)*
- [x] T05 · Add CLI tests, wire `time-table`, and document input/exit behaviour. *(SPEC-001-B06; plan step 5)*
- [x] T06 · Update architecture/component docs and run the full verification suite. *(SPEC-001-B01–B06; plan step 6)*
- [x] T07 · Add AC1–AC2 tests for raw metadata, signed epochs and precision errors, including a FILETIME input between datetime microseconds. Then implement exact direct conversion and preserve existing exact callers. *(SPEC-001-B03; plan step 7)*
- [x] T08 · Add AC4–AC5 tests for the exact gap boundary, the offset one microsecond earlier and both historically variable dates. Then implement declared site policies and bounded gap resolution. *(SPEC-001-B01, B02; plan step 8)*
- [x] T09 · Add AC3 tests for both local forms, including ordinary, missing-site, repeated and skipped readings. Then add and wire the application codec. *(SPEC-001-B03, B04; plan step 9)*
- [x] T10 · Add AC6 tests for malformed dates and UTC range failures with empty stdout and one diagnostic naming the site and date. Then tighten CLI validation and error handling. *(SPEC-001-B06; plan step 10)*
- [x] T11 · Update documentation, synchronise generated status and verify PBI-001-24. Confirm RT07 and clock-fault regressions still pass. *(SPEC-001-B01–B06; plan step 11)*

## Loop limits

The default remains: after **3** consecutive `poetry run sdd verify 001` failures on the same task, stop and ask the mentor and mentee.
