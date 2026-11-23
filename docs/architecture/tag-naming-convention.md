# Orion synthetic tag naming convention

Version 1 defines canonical spellings for the synthetic plant. The generator deliberately
varies source names to exercise reconciliation. The join key for current source rows is
`(site_code, original_name)`. A spelling can occur at more than one site and point to
different equipment there.

## Canonical grammar

| Point | Format | Example |
|---|---|---|
| Operational | `<SITE>.<AREA>.<EQUIPMENT>.<INSTRUMENT>.<SIGNAL>` | `ORN.A200.R201.TIC-2011.PV` |
| Laboratory | `<SITE>.LAB.<AREA>.<SAMPLEPOINT>.<ANALYTE>` | `BEL.LAB.A200.AH207.PH` |

The parser requires an exact match, using ASCII letters and digits with case significant
and dots between segments. Rendering a parsed value reproduces the input.

| Token | Version 1 rule |
|---|---|
| Site | `ORN` Brazil, `GUL` US Gulf Coast, `BEL` Belgium, `CHN` China, `IND` India |
| Area | `A` followed by three digits, beginning with a nonzero digit |
| Equipment or sample point | One or two uppercase letters followed by three digits, beginning with a nonzero digit |
| Instrument | One of the instrument labels below, a hyphen, and exactly four digits |
| Signal | `PV` process value, `SP` setpoint, `OUT` controller output, `MODE` operating mode, `ALM` alarm state |
| Analyte | `PH`, `H2O`, `CL`, `SOL`, or `RHO` |

The fixture uses ISA-style labels `TIC`, `FIC`, `PIC`, and `LIC` for temperature,
flow, pressure, and level control respectively. It uses `TI`, `PI`, `FI`, `EI`, `AI`,
`QI`, and `ZI` for temperature, pressure, flow, energy, analysis, quality, and position
indication. The generator takes the three digits from the equipment code and appends
`0` to form its instrument number. Signal roles sharing that number remain separate plant
points. The grammar also accepts four-digit numbers such as the example above.

## Source variations

| Tier | Variation |
|---|---|
| Convention | Keep the canonical spelling. |
| Site dialect | Drop the area, replace dot separators, lowercase the name, glue equipment and instrument, use a legacy site abbreviation, or use a different signal suffix. |
| Site dialect | Omit the site abbreviation to reserve selected identical names across sites. |
| Ad hoc | Use a numeric-only name or free-text label, transpose characters, or rename a legacy tag. |

| Site | Alternate separator | Legacy prefix | Preferred dialect form |
|---|---|---|---|
| Brazil | `_` | `BRZ` | Alternate separator |
| US Gulf Coast | `/` | `USGC` | Glued equipment and instrument |
| Belgium | `-` | `BE` | Legacy abbreviation |
| China | `:` | `CN` | Dropped area |
| India | `_` | `IN` | Lowercase |

The builder targets 60% convention, 25% dialect, and 15% ad hoc. It reserves 15 shared
names across different sites and equipment, then reserves at least 20 distinct points per
other variation before filling the tier quotas. It reserves both current names and old
aliases per source and rejects an input whose capacity cannot meet the floors.

Each current source row carries its reported descriptor and unit. The builder uses
Portuguese vocabulary for Brazil and English elsewhere. It leaves at least 5% of
descriptors blank and at least 5% of reported unit spellings blank or noncanonical.
The reference retains the canonical unit and which variations the generator applied.

## Reference boundary

The private reference maps the source-scoped key to the canonical name, equipment and
instrument IDs, and the loop ID when the point has an explicit role. A legacy rename is
represented by the replacement's current source row and the old alias and fixed instant
`2025-01-01T00:00:00Z` in that row's private reference. Hold-out selects one site
and is also recorded in the private reference.

See [ADR-0031](decisions/0031-separate-the-consumer-catalogue-from-plant-truth.md) and the
[approved contract](../../specs/004-plant-tag-catalogue/plan.md#contracts-and-data).
