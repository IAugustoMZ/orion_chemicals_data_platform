# Validation · 004 · Plant and tag catalogue

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

On 2026-11-23, `poetry run sdd verify 004` passed on Git commit `7075286`, the merge
commit of card 03. The harness binds G5 to the governed-code digest `7d084d8dde7a`.

| Check | Verdict |
|---|---|
| Formatting and lint | Pass for Ruff formatting, lint, docstrings and complexity |
| Static types and architecture | Pass for strict mypy and import-linter |
| Tests | 389 passed with 95.86% coverage against the 85% threshold |
| Security and secrets | Pass for Bandit and detect-secrets |
| Dependency audit | Pass for pip-audit with network access |
| Harness and documentation | Pass for `sdd check` and strict MkDocs build |

## Code review

The independent reviewer inspected the implementation range `06bf228..7075286` and reran
56 focused tests. Source keys and aliases are reserved within each site, collision fixtures resolve
to distinct equipment, and the export rejects nonunique or mismatched key sets before staging.
The catalogue schema fixes the shared fields and types, and the reference holds the UTC rename
instant and private labels. The applications use narrow ports wired in bootstrap.

One finding remains open pending independent confirmation of the fix. The reviewed catalogue
writer forwarded the text of caught OS and Arrow exceptions to the CLI. See the
[security finding below](#security-review) and the corrective
[PBI-004-04](backlog.md#pbi-004-04--redact-internal-paths-from-catalogue-errors).

## Architecture review

The review confirmed the planned domain, application, CLI, bootstrap and adapter boundaries.
The plant builder remains independent of the catalogue builder and external libraries. Bootstrap
injects the seeded draws and both writers, and the export use case coordinates the builders.
[ADR-0031](../../docs/architecture/decisions/0031-separate-the-consumer-catalogue-from-plant-truth.md)
covers both file boundaries and the local single-writer publication contract. The teaching-guide
diagram now shows both builders working with the plant model.

## Security review

| Threat | Evidence |
|---|---|
| Spoofing | Declared site codes, deliberate cross-site name collisions, and rejection of duplicate and mismatched export keys. |
| Path redirection | Both writers reject symlinks at fixed child paths. The operator controls the output directory and its parents. |
| Partial publication | Both staged files are validated before replacement. Failure injection confirms preservation on staging failure and recovery after interruption between replacements. |
| Repudiation | Explicit seed and version reproduce the fixture. The local commands introduce no authenticated actor or audit endpoint. |
| Information disclosure | Both private files were mode `0600`. Exact schema checks keep private labels out of the consumer file. Catalogue errors exposed filesystem paths in the reviewed revision. |
| Denial of service | The fixture and naming allocations are bounded. Tests exercise insufficient profiles and invalid seeds. |
| Elevation of privilege | The writers run with the caller's permissions under the trusted destination. Both existing Compose hardening tests passed. |

The catalogue writer's exception handler included raw exception text in the reviewed revision.
Running `catalog build` with `--out` pointing to an existing
temporary file reproduced exit 1 and empty stdout, but stderr included the full path with the
internal `catalog` child appended. That conflicts with the
[security baseline](../../harness/security.md#4-inputs-and-outputs). Treat this as a blocker for G6.
Use fixed, operation-specific diagnostics, retain the original cause internally, and cover the
public error with regression tests. Card 04 implements this recommendation in the
[catalogue writer](../../src/tssource/infrastructure/catalogue_parquet.py).
All 20 catalogue CLI tests passed, and `poetry run sdd item verify 004 04` passed both
acceptance criteria and the full quality suite. Independent validation of the fix follows merge.

## Functional validation

Independent QA ran 58 focused tests with `--no-cov`. An initial focused run passed all tests
but exited with the global coverage threshold because the selection omitted unrelated modules.
Full-suite coverage is recorded under G5.

| Behaviour or RT | How validated | Result |
|---|---|---|
| B01 | `test_inventory_reconciles` | Pass. Five sites reconcile with the equipment and scan-class counts. |
| B02 | `test_same_seed_reproduces_the_model`, `test_different_seeds_change_ids` and two clean seed-42 CLI runs | Pass. Same-seed JSON bytes match and different seeds change IDs. |
| B03 | `test_topology_resolves_in_each_area`, `test_scan_policy_matches_interval` | Pass for loop roles, streams, drivers and scan intervals. |
| B04 | `test_cli_writes_only_the_versioned_private_model` | Pass for footprint, mode, version, generator marker and stdout. |
| B05 | `test_canonical_round_trip`, `test_parser_rejects_malformed_names` and catalogue tier, variation and metadata tests | Pass for both forms, coverage floors, missing descriptors and reported-unit variants. |
| B06 and RT09 | `test_cross_site_collisions_have_distinct_equipment`, `test_unique_join_and_plant_ids`, `test_writer_rejects_invalid_keys_before_staging` | Pass for fixture identities and conflict rejection. Production mapping enforcement remains separate. |
| B07 | `test_composed_catalogue_repeats_with_one_holdout_site`, `test_renamed_tags_retain_private_history` | Pass for reproducible rows, one hold-out site and private rename history. |
| B08 | `test_exports_exact_versioned_schemas` | Pass for both v1 schemas, private fields and paths. |
| B09 and RT17 | `test_exports_reconcile_with_same_seed_plant` at seeds 0, 42 and 101 | Pass for identity and scan policies. Lab and exception tags have no periodic interval. Completeness calculations remain separate. |
| B09 and RT28 | Same-seed installed CLI builds, then grouped counts over plant JSON and both Parquet outputs | Pass for fixture sizing inputs. A full capacity worksheet remains separate. |
| B10 | `test_failed_staging_preserves_previous_pair`, `test_writer_rejects_inconsistent_staged_footer`, `test_failed_replace_reports_safe_error_and_retry_restores_pair`, `test_symlinks_at_fixed_paths_are_rejected` | Original QA passed staging, retry and fixed-path guards. Independent validation of the card 04 stderr fix is pending. |

The two clean seed-42 builds produced 2,050 rows in each Parquet file. Every source
and name key joined to exactly one reference row and the correct equipment in the plant.
Counts were 700 for Brazil, 450 for US Gulf Coast, 350 each for Belgium and China, and 200
for India. Periodic counts were 186 at 1, 5 and 10 seconds each, 391 at 30 seconds, 224 at
60 seconds, 205 at 300 seconds, and 186 at 900 seconds. The remaining 391 exception points
and 95 lab points had null intervals. There were 15 distinct shared names and 77 rename rows.
An invalid seed exited 2 with empty stdout and created no output.

## Documentation upkeep

- [x] ADR-0031 records the sharing and publication decisions.
- [x] Architecture pages describe the modules, data relationships and command sequences.
  The diagrams retain the registered tool logos.
- [x] The root README lists both commands. The harness regenerated the status and traceability pages.
- [x] The component README documents the commands and schemas. The contribution workflow
  continues to use the existing single-card instructions.
- [x] The teaching guide covers both commands, including the corrected builder diagram.

## Build log

1. Card 01 built the private plant and JSON CLI (PR #31, `a404bae`).
2. Card 02 added source-scoped naming and private mappings (PR #32, `62e9968`).
3. Card 03 added the two versioned Parquet exports and covered staged failures, path
   redirection and retry (PR #33, `b7af6cf`).
4. The harness recorded all three merges. The full dossier verification passed on its first
   run after the final merge.

## Review notes (optional)

_Nothing needed to approve. Add a line here (or use `--note` when approving) only for a
condition on the merge or a decision worth remembering._
