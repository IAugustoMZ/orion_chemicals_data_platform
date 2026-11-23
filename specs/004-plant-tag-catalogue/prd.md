# PRD · 004 · Plant and tag catalogue

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/004-plant-tag-catalogue/` · branch `spec/004-plant-tag-catalogue` · kind **feature** · created 2026-11-23.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT09 | P | Original identifiers shall be stored with their source; the combination source + code shall never point to two pieces of equipment at the same time. | Try to insert a conflicting mapping and verify that it is rejected. |
| RT17 | P | Completeness shall only be computed when the expected frequency or quantity is defined. | Do not apply the same denominator to a periodic tag and to a report-by-exception tag. |
| RT28 | P | Sizing shall declare tags, frequencies, average size, history, concurrency and growth, separating measurement from projection. | A capacity spreadsheet with traceable inputs and a matching test. |

This dossier supplies synthetic evidence for three prototype requirements. Source and original
tag name together identify a point, including when two sites use the same name (RT09). The
catalogue declares sampling expectations (RT17), and measured tag counts by site and scan class
become inputs to later capacity estimates (RT28).

Platform conflict enforcement and completeness calculation belong to later ingestion and quality
work. Source contracts (RT02), unresolved identifiers (RT10), unit conversion (RT13), throughput
(RT29) and answer-key audit controls (RT38) are separate. RT01 and RT36 still apply. All data is
fictional and the generator requires no industrial connection or credentials.

## Problem

The ingestion engineer needs a realistic fixture before real sources are available. Globally
unique tag names hide collisions. A fixture where every tag samples on a schedule gives
completeness checks a misleading denominator. The team also needs a reference mapping to tell
whether a future identity model associated a reading with the correct equipment.

## Goals and success metrics

The baseline is the merged generator skeleton and time core. Neither produces a plant-derived
tag catalogue or reference mapping.

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| Reproduce a plant | Counts, identifiers and loop references | No plant model | Five sites, about 2,050 points, with per-site counts within 10% of the declared profile and at least 10 instruments per equipment class. Same seed reproduces the model. A different seed changes surrogate IDs. Each loop resolves its three roles in one area. | Compare fixed-seed builds, count points and check references. |
| Exercise identity matching | Naming mix, variation coverage and collision counts | No tag catalogue | Convention, site dialect and ad hoc shares within five percentage points of 60%, 25% and 15%. At least 1,000 canonical names, 20 examples per declared violation type and 15 cross-site name collisions pointing to different equipment. Canonical names round-trip. | Group by tag and site, reconcile with the reference and parse and render canonical names. |
| Declare sizing inputs | Counts and expectations by site and scan class | Benchmark uses random-walk data | Catalogue counts reconcile with the model. Periodic classes declare an interval. Exception-based and lab tags carry no assumed periodic denominator. | Compare counts by site and scan class and inspect examples of each sampling mode. |
| Preserve metadata variation and reference separation | Missing metadata rates and public schema | No paired catalogue and reference | At least 5% empty descriptors and 5% empty or unusual unit spellings. The consumer file excludes private fields and the hold-out flag. | Inspect generated counts, schemas and output paths. |

## Users and scenarios

- **Ingestion engineer.** Receives the same tag name from two sites and uses the source to keep
  the records distinct. The private reference identifies the equipment in each case.
- **Capacity planner.** Counts one-second points separately from slower, exception-based and lab
  points before estimating data volumes.
- **Model evaluator.** Uses the consumer catalogue as input and reserves the reference mapping
  and hold-out designation for later evaluation.

## Scope

### In scope

- A seeded plant across Brazil, the US Gulf Coast, Belgium, China and India, with areas,
  equipment, instruments, control loops, flows and shared driver relationships for later signals.
  The inherited default profile allocates approximately 700, 450, 350, 350 and 200 points.
- The versioned naming convention, site dialects, ad hoc variants, English or Portuguese
  descriptors and varied unit spellings from original roadmap cards 06 and 07.
- Local artifacts. The plant model lives in `truth/plant.json`, consumers read
  `catalog/tags.parquet`, and `truth/tag_key.parquet` maps the tags to the private reference.

### Out of scope

- Signal values, physics simulation, acquisition, real sources and profiles larger than the default.
- Platform identity enforcement, unknown-tag handling, completeness calculation, unit conversion
  and a full capacity or throughput report.
- Model training and the broader answer-key leak guard assigned to separate roadmap card 08.

## Constraints and assumptions

- Reuse the merged `tssource` skeleton and the local Poetry and Docker Compose workflow.
  English and Portuguese descriptors are synthetic fixture values.
- Inherit deterministic seed handling, a synthetic-data marker, card-by-card approvals and a
  specification limited to 50 lines.
- Treat each fictional site as one source namespace. Cross-site collisions are deliberate.
  Each source and tag name pair resolves to a single equipment identity at a given time.
- Define multiple source namespaces within one site in the later source-contract dossier.
  Lab tags in this fixture declare a lab scan class with no expected interval.
- If scope needs to shrink, relax the 60/25/15 naming mix first while keeping convention names
  in the majority and retaining the floors for naming variations and cross-site collisions.
- Measure counts on the generated fixture and keep growth and storage projections separate.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| Seeded samples omit rare variants or collisions | A realistic-looking catalogue misses known failure modes | Mentee checks the coverage floors across several fixed seeds. |
| A site later needs multiple source namespaces | Site alone would be too broad an identity key | Mentee checks the identity key when defining the later source contracts. |
| A later lab profile introduces an agreed schedule | An unset interval would omit expected samples from completeness | Mentor reviews any proposed scheduled lab profile with its source contract. |
| Reference fields reach the consumer dataset | Later evaluation may score leaked answers | Mentee verifies file and schema boundaries. The separate leak-guard card owns broader enforcement. |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
