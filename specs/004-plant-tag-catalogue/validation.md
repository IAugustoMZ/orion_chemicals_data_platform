# Validation · 004 · Plant and tag catalogue

> Written during **Phase 5 · Build** and **Phase 6 · Validate**; approved with the teaching
> guide at **G6 · Approved for merge** (both of us approve). Reviews are independent: the
> reviewer is not the agent or person that built the change.
> How to fill this file: [lifecycle, phase 6](../../harness/lifecycle.md#phase-6-validate).

## Verification (G5)

On 2026-11-23, `poetry run sdd verify 004` passed on Git commit `5fab8ff`, the merge
commit of card 05. The harness binds G5 to the governed-code digest `ae2f173d8d22`.

| Check | Verdict |
|---|---|
| Formatting and lint | Pass for Ruff formatting, lint, docstrings and complexity |
| Static types and architecture | Pass for strict mypy and import-linter |
| Tests | 395 passed with 95.87% coverage against the 85% threshold |
| Security and secrets | Pass for Bandit and detect-secrets |
| Dependency audit | Pass for pip-audit with network access |
| Harness and documentation | Pass for `sdd check` and strict MkDocs build |

## Code review

The independent reviewer inspected the implementation range `06bf228..7075286` and reran
56 focused tests. Source keys and aliases are reserved within each site, collision fixtures resolve
to distinct equipment, and the export rejects nonunique or mismatched key sets before staging.
The catalogue schema fixes the shared fields and types, and the reference holds the UTC rename
instant and private labels. The applications use narrow ports wired in bootstrap.

The independent follow-up reviewed `7075286..4dd0ab0` and passed all 20 catalogue CLI tests.
The corrective [PBI-004-04](backlog.md#pbi-004-04-redact-internal-paths-from-catalogue-errors)
keeps exception translation in the writer and preserves the cause. The reviewer confirmed
the fixed messages for ordinary staging and replacement failures.

**Low severity, accepted for the prototype in the G6 discussion.** If replacement and staging-file cleanup both fail,
the [writer's cleanup handling](../../src/tssource/infrastructure/catalogue_parquet.py#L64)
can supersede the artifact-specific publication error in AC2. The reviewer injected both
failures and observed exit 1, empty stdout, and a generic path-free diagnostic. If artifact
identification is required for combined failures, preserve the primary diagnostic when cleanup
also fails.

## Architecture review

The review confirmed the planned domain, application, CLI, bootstrap and adapter boundaries.
The plant builder remains independent of the catalogue builder and external libraries. Bootstrap
injects the seeded draws and both writers, and the export use case coordinates the builders.
[ADR-0031](../../docs/architecture/decisions/0031-separate-the-consumer-catalogue-from-plant-truth.md)
covers both file boundaries and the local single-writer publication contract. The teaching-guide
diagram now shows both builders working with the plant model. The follow-up confirmed that
the corrective card leaves layer wiring, dependencies, schemas, permissions and publication
order intact. The independent review of card 05 confirmed that the root-anchored MkDocs
exclusions control which files are published. The container service and its mount remain
as specified.

## Security review

| Threat | Evidence |
|---|---|
| Spoofing | Declared site codes, deliberate cross-site name collisions, and rejection of duplicate and mismatched export keys. |
| Path redirection | Both writers reject symlinks at fixed child paths. The operator controls the output directory and its parents. |
| Partial publication | Both staged files are validated before replacement. Failure injection confirms preservation on staging failure and recovery after interruption between replacements. |
| Repudiation | Explicit seed and version reproduce the fixture. The local commands introduce no authenticated actor or audit endpoint. |
| Information disclosure | Both private files were mode `0600`. Exact schema checks keep private labels out of the consumer file. The follow-up verified path-free stderr for the original disclosure and for simultaneous replacement and cleanup failures. MkDocs excludes the root fixture and draft trees even when their files are readable. |
| Denial of service | The fixture and naming allocations are bounded. Tests exercise insufficient profiles and invalid seeds. |
| Elevation of privilege | The writers run with the caller's permissions under the trusted destination. Both existing Compose hardening tests passed. |

The catalogue writer's exception handler included raw exception text in the reviewed revision.
Running `catalog build` with `--out` pointing to an existing
temporary file reproduced exit 1 and empty stdout with the full output path in stderr.
Card 04 applies the [security baseline](../../harness/security.md#4-inputs-and-outputs) through
fixed diagnostics and internal exception chaining. The independent reviewer repeated the same
installed CLI command against `4dd0ab0`. It exited 1 with empty stdout and stderr containing
only `error: could not stage tags.parquet`. The original disclosure is closed.

## Functional validation

Independent QA reran the plant, naming, catalogue CLI and Compose hardening suites on
`4dd0ab0`. All 62 focused tests passed with `--no-cov`. Full-suite coverage is recorded under G5.

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
| B10 and card 04 | Focused catalogue CLI tests, plus installed CLI probes with a regular file as the destination and a directory obstructing each target in turn | Pass for staging preservation, both replacement errors, same-seed retry and fixed-path guards. See the code review for the combined-failure diagnostic. |
| Card 05 AC1 and AC2 | `test_docs_site_outputs.py` and a real checkout build with `poetry run mkdocs build --strict --quiet --site-dir <isolated-site>` | Pass. Readable stand-ins were excluded by file selection and from built output. The real checkout contained the three persisted artifacts and local drafts. The built site included its index, and neither excluded tree appeared. |

The two clean seed-42 builds produced 2,050 rows in each Parquet file. Every source
and name key joined to exactly one reference row and the correct equipment in the plant.
Counts were 700 for Brazil, 450 for US Gulf Coast, 350 each for Belgium and China, and 200
for India. Periodic counts were 186 at 1, 5 and 10 seconds each, 391 at 30 seconds, 224 at
60 seconds, 205 at 300 seconds, and 186 at 900 seconds. The remaining 391 exception points
and 95 lab points had null intervals. There were 15 distinct shared names and 77 rename rows.
An invalid seed exited 2 with empty stdout and created no output. In the follow-up, both
replacement probes exited 1 with empty stdout and the correct fixed artifact diagnostic.
An injected preparation failure also exited 1 with empty stdout and path-free stderr,
preserving both previously published files.
The reference stayed intact when consumer publication failed. A reference replacement failure
left the new consumer in place. QA found no orphan staging files in either probe. After
clearing the obstruction, a seed-101 retry produced two files that byte-matched a clean
seed-101 export and shared 2,050 unique keys.

Independent QA passed both focused tests and confirmed that MkDocs excludes all three fixture
files and nine local draft and media files. The built site contained the home and deployment
pages. The independent reviewer confirmed both exclusions in the built site. The harness invokes
the strict build with `--quiet`. Running without that flag reports four existing relative
link warnings in the dossier 003 teaching guide and dossier 004 plan, which cause a
nonquiet strict build to exit 1. Those links predate card 05. The exclusion applied in
both runs.

## Documentation upkeep

- [x] ADR-0031 records the sharing and publication decisions.
- [x] Architecture pages describe the modules, data relationships and command sequences.
  The diagrams retain the registered tool logos.
- [x] The root README lists both commands. The harness regenerated the status and traceability pages.
- [x] The component README documents the commands and schemas. The contribution workflow
  continues to use the existing single-card instructions.
- [x] The teaching guide covers both commands, including the corrected builder diagram.
- [x] The root and component READMEs and the deployment page cover bind mount provisioning and
  the write preflight. ADR-0008 and the site tutorial record the MkDocs exclusions.

## Build log

1. Card 01 built the private plant and JSON CLI (PR #31, `a404bae`).
2. Card 02 added source-scoped naming and private mappings (PR #32, `62e9968`).
3. Card 03 added the two versioned Parquet exports and covered staged failures, path
   redirection and retry (PR #33, `b7af6cf`).
4. The harness recorded the first three merges, and dossier verification passed on `7075286`.
5. Independent review found a path disclosure in catalogue errors. Card 04 fixed it and added
   CLI regression coverage (PR #35, `ee6bab4`). GitHub CI passed and the harness recorded the merge.
6. After card 04 merged, the first dossier verification hit a `/tmp` disk quota during the Parquet
   benchmark. The unchanged suite passed on retry with `TMPDIR` on the workspace filesystem.
7. Release checks found an unwritable default bind mount. Provisioning its empty root for the
   service UID fixed default writes. With the generated files in place, G5 exposed an attempt
   to copy them into the documentation site.
8. Card 05 excluded the root fixture and draft trees and covered both MkDocs file selection and
   emitted site files (PR #38, `964a69b`). GitHub CI passed. The full G5 suite passed on
   `5fab8ff` with the default output files still on the bind mount.

## Review notes (optional)

- Accept the generic path-free diagnostic when publication and staging-file cleanup both fail.
  Revisit artifact identification if operators need it for recovery.
- Keep one writer per destination and retry with the intended seed. Revisit publication if
  readers need access during writes.
- Use the measured tag counts and scan intervals as RT28 fixture-sizing inputs. Evaluate
  industrial capacity in a separate benchmark.
