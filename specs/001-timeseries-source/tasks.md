# Tasks · 001 · Time-series source: global time core

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. During the build, tick the boxes: ticking does not invalidate G4, but rewording, adding or removing a task does.

## Tasks

- [ ] T01 · Add failing site-zone and local-resolution transition tests, then implement the pure domain values. *(SPEC-001-B01, B02; plan step 1)*
- [ ] T02 · Add the zone-resolver port and `zoneinfo` adapter; make the DST tests pass. *(SPEC-001-B01, B02; plan step 2)*
- [ ] T03 · Add failing codec tests, then implement the six representations and explicit local-text decoding. *(SPEC-001-B03, B04; plan step 3)*
- [ ] T04 · Add failing three-time and clock-fault tests, then implement their value objects. *(SPEC-001-B05; plan step 4)*
- [ ] T05 · Add CLI tests, wire `time-table`, and document input/exit behaviour. *(SPEC-001-B06; plan step 5)*
- [ ] T06 · Update architecture/component docs and run the full verification suite. *(SPEC-001-B01–B06; plan step 6)*

## Loop limits

The default remains: after **3** consecutive `poetry run sdd verify 001` failures on the same task, stop and ask the mentor and mentee.
