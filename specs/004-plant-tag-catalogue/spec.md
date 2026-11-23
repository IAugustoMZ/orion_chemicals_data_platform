# Execution specification · 004 · Plant and tag catalogue
## Context collected
| Source | Contribution |
|---|---|
| [Context and constraints](plan.md#context-collected) | RT09, RT17, RT28, approved artifacts, the merged generator, and inherited ADRs. |
## Behaviour
| ID | EARS behaviour | RT / criteria |
|---|---|---|
| SPEC-004-B01 | When built with the default profile, the plant shall contain five sites within 10% of their declared point counts, at least 10 instruments per equipment class, and a reconciled inventory by site and scan class. | RT28 / 01 AC1 |
| SPEC-004-B02 | When built twice from the same seed, the plant shall reproduce the model and JSON bytes. When the seed changes, corresponding equipment and instrument IDs shall change. | RT28 / 01 AC2–AC3 |
| SPEC-004-B03 | The plant shall resolve all loop roles within their area, all flow endpoints, and all shared-driver links. It shall declare the interval for periodic classes and null for lab and exception classes. | RT17, RT28 / 01 AC4–AC5 |
| SPEC-004-B04 | When plant build succeeds, it shall write only the versioned, synthetic `truth/plant.json` and print its path. | RT28 / 01 AC6 |
| SPEC-004-B05 | When a canonical instrument or lab name is parsed and rendered, it shall round-trip. The default fixture shall meet the approved tier, naming-variation and descriptor/unit targets. | RT09, RT28 / 02 AC1–AC3, AC6 |
| SPEC-004-B06 | When the catalogue is built, it shall return one record per point, unique by site and current name, with 15 or more cross-site names pointing to distinct equipment at each affected site. | RT09, RT28 / 02 AC4–AC5 |
| SPEC-004-B07 | When built from the same plant and seed, the catalogue and reference shall reproduce all rows and the private hold-out site. A legacy rename shall retain the old alias and replacement instant in the reference. | RT09 / 02 AC7–AC8 |
| SPEC-004-B08 | When catalogue build succeeds, it shall publish only the two versioned files on their declared paths and print both paths. The consumer schema shall exclude private fields. | RT09 / 03 AC1–AC2 |
| SPEC-004-B09 | When the exported files are joined by site and name, every consumer row shall match one reference and same-seed plant point. Counts and intervals shall match the inventory and scan policies. | RT09, RT17, RT28 / 03 AC3–AC4 |
| SPEC-004-B10 | If either file fails staging, the CLI shall return a handled error and preserve existing files. If replacement fails, it shall report failure with empty stdout. A successful same-seed rerun shall restore the pair. | RT09 / 03 AC5 and G3 |
## Architecture impact
| Boundary | Change |
|---|---|
| [Before and after](plan.md#architecture-impact) | Add two local build commands, pure generation, and dedicated JSON and Parquet writers. Reuse the existing dependencies and runtime. |
## Contracts and data
| Contract | Shape and access |
|---|---|
| [CLI, three files, and relationship diagram](plan.md#contracts-and-data) | Local outputs use schema version 1. The public and private rows share the source and name key. |
## Design
| Source | Responsibility |
|---|---|
| [Layer design and class diagram](plan.md#design) | Pure plant and naming rules. Bootstrap injects repeatable variation draws and output writers. |
## Security and threat model
| Source | Verification |
|---|---|
| [STRIDE table](plan.md#security-and-threat-model) | Verify declared sites, safe output paths, bounded generation, restricted truth files and consumer schema. |
## Validation plan
| Source | Coverage |
|---|---|
| [Test matrix](plan.md#validation-plan) | Every behaviour and cited RT has fixture-level evidence. Platform enforcement, completeness calculations, and full capacity planning follow later. |
## Architecture decisions
[ADR-0031](../../docs/architecture/decisions/0031-separate-the-consumer-catalogue-from-plant-truth.md) proposes separate consumer and reference files generated from the same seeded plant.
## Documentation impact
[Upkeep](plan.md#documentation-impact) covers the root and component READMEs, architecture, naming rules, schemas and teaching guide.
## Out of scope
[Exclusions](plan.md#out-of-scope) cover live sources, signals, production rules, training, leakage controls and capacity claims.
