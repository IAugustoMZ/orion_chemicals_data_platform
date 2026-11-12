# Implementation plan · 002 · Harness: item-by-item flow and CI
> Part of **Phase 4 · Specify**, approved with the spec at **G4**.
## Approach
Card by card in backlog order, test first. Card 01 is built on this spec branch because it unblocks commits; from card 02 on, each card gets its own branch and pull request, merged by a person.
## Steps
1. Card 01: `has_teaching_guide` in the report, status generator, `sdd sync` (SPEC-002-B01).
2. Card 02: domain, use cases, YAML adapter, `sdd item status|verify`, AC marker (B02).
3. Card 03: `GitRepository`, `NextItem`, `MarkItemMerged`, guard rules, docs, skill (B03, B04).
4. Card 04: `ci.yml`, `verify --no-record`, `.github/` governed, ADR-0024 accepted, manual proof (B05).
5. Card 05: rationale required in domain, use case and CLI help (B06).
## Files to create or change
- domain: `item_progress.py`, `card_digest.py`, `dossier.py`, `governance.py`; application: use cases, ports, generators.
- infrastructure: `yaml_progress_repository.py`, `git_cli_repository.py`; interfaces: CLI group `item`.
- tests: `tests/sdd/` files named in each card; `.github/workflows/ci.yml`; docs and skills as in the spec.
## Rollback
Revert the merge commit of the card; no data is written outside `specs/`.
## Risks during the build
- New G2/G5 rules break dossier 000: signal is a failing old test; keep the no-`progress.yaml` path.
- A temporary git repository test is flaky on Windows: use argument lists and `tmp_path` only.
