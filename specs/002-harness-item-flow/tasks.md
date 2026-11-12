# Tasks · 002 · Harness: item-by-item flow and CI
> Part of **Phase 4 · Specify**, approved with the spec at **G4**. Ticking boxes does not make G4 stale; rewording does.
## Tasks
- [x] T01 · Card 01: tests, then `has_teaching_guide` and status link, `sdd sync` *(SPEC-002-B01, step 1)*
- [ ] T02 · Card 02: tests, then domain, use cases, YAML adapter, `item status|verify`, AC marker *(B02, step 2)*
- [ ] T03 · Card 03: tests, then git port and adapter, `item next|merged`, guard rules *(B03, B04, step 3)*
- [ ] T04 · Card 03: update AGENTS.md, lifecycle, gates, how-it-works, skill `sdd-next-item`, ADR-0023 *(B03, step 3)*
- [ ] T05 · Card 04: tests, then `ci.yml`, `verify --no-record`, governed `.github/` *(B05, step 4)*
- [ ] T06 · Card 04: ADR-0024 accepted, ADR-0004 superseded, docs, branch-protection checklist, manual proof *(B05, step 4)*
- [ ] T07 · Card 05: tests, then rationale required, CLI help, docs *(B06, step 5)*
## Loop limits
Default: after **3** consecutive failing `sdd verify 002` runs on the same task, stop and ask us.
