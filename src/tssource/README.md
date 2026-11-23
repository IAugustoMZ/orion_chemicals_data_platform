# tssource · global plant data generator

Component of dossier [003](../../specs/003-tssource-skeleton-spike/spec.md) (child of umbrella
001). Card 01 delivered the package skeleton; card 02 added `tssource bench`.

| Layer | Folder | Holds |
|---|---|---|
| domain | `domain/` | pure rules, plant profiles and `TssourceError` |
| application | `application/` | use cases, ports, immutable `Settings` |
| infrastructure | `infrastructure/` | adapters (numpy, pyarrow, files) |
| interfaces | `interfaces/cli/` | the Typer command line |
| root | `bootstrap.py` | the only place that wires |

```bash
poetry install --with tssource          # once
poetry run tssource --help              # plant, run, bench, config, report, health, time-table
poetry run tssource time-table --site us-gulf-coast --date 2024-03-10
poetry run tssource plant build --seed 42 --out data/ts_source
mkdir -p data/ts_source                 # the one writable folder of the container
docker compose up --build tssource      # idles, reported healthy
docker compose run --rm tssource --help
docker compose run --rm tssource bench --format parquet --seconds 60 --out /data/ts_source/parquet
```

`bench` writes events through one serialiser (`jsonl-gzip`, `jsonl` or `parquet`) for `--seconds`
of wall time, deletes its scratch file and leaves `bench.json` (version 1: events per second as
mean, p50, p95, p99 and minimum, events, CPU seconds, peak memory, floor, bottleneck). It exits 3
and names the bottleneck stage when the mean is below 25,000 events/s. Measured results: see
[ADR-0028](../../docs/architecture/decisions/0028-writer-choice-after-the-throughput-spike.md).

Settings come from `TSSOURCE_SEED`, `TSSOURCE_OUT`, `TSSOURCE_MODE`, `TSSOURCE_START`,
`TSSOURCE_END` and `TSSOURCE_SPEED_FACTOR`. Exit codes: 0 success, 1 not implemented or a
handled error, 2 usage, 3 benchmark floor missed.

`time-table` is a read-only civil-time diagnostic. It prints all local top-of-hour values for a
site and date, their explicit `ok`, `ambiguous`, or `gap` outcome, retained UTC candidate(s), and
offset(s). A gap retains the requested wall-clock value and shows the first valid UTC instant;
a repeated hour shows both UTC candidates. The date must use ASCII `YYYY-MM-DD`. Invalid dates
and dates that would put any row outside the UTC calendar range exit with code 2 before printing
the table.

Brazil, the US Gulf Coast, and Belgium use their declared IANA zones. The fictional China and
India sites use fixed offsets of `+08:00` and `+05:30` for every supported date. In-process callers
can get the shared `TimestampCodec` from `tssource.bootstrap.build_timestamp_codec()`. It handles
six source forms, preserves the original value and its source zone or offset on decode, and raises
`ValueError` for an invalid or inexact conversion. ISO-offset input accepts `Z`, signed offsets
such as `+05:30` and `+0530`, and representable fractions on explicit seconds such as
`+00:00:00.5`. Invalid fields such as `+00:60` and shortened fractions such as `+00:00.5` raise
`ValueError`. Both offset-free formats require a declared site.
See [the time contracts](../../specs/001-timeseries-source/plan.md#time-contracts).

## Private plant fixture

`plant build` prints the path to `OUT/truth/plant.json` after writing it. The seed must be a
nonnegative integer. Omitted options use `TSSOURCE_SEED` (42) and `TSSOURCE_OUT` (`data/ts_source`).
The file is deterministic for a given seed and locked version. It is restricted evaluation
material. Keep it under an operator-owned destination and use one writer per destination.
Inside the container, use `--out /data/ts_source` under the existing writable bind.

The UTF-8 JSON contract has `schema_version` 1 and `generator` set to `tssource`. The ordered
collections are `sites`, `areas`, `equipment`, `instruments`, `control_loops`, `streams`,
`drivers` and `inventory`. IDs link equipment to areas, points to equipment, loop roles to
points, and streams to equipment. A driver is a shared influence in one area. Each inventory
row gives the observed point count for one site and scan class.

Each point declares its measurement, engineering range, canonical unit, data type and scan
class. Intervals are 1, 5, 10, 30, 60, 300 or 900 seconds for periodic classes and JSON `null`
for lab and report-by-exception points. See [the topology diagram](../../docs/architecture/README.md#32-private-plant-inventory)
and the [approved contracts](../../specs/004-plant-tag-catalogue/plan.md#contracts-and-data).

The writer stages a complete file before replacing the previous version and sets mode `0600`
on Linux. It refuses symlinks at `truth/` and `truth/plant.json`. A generation or write failure
exits 1 with a diagnostic on stderr and empty stdout. Invalid arguments or settings exit 2.

## Tag catalogue generation

In-process callers can use `build_catalogue_builder(seed).build(plant)` from the composition
root to derive the current catalogue records and the private reference together. Build the
plant with the same explicit seed for repeatability. Both sets of rows use the
`(site_code, original_name)` key, including when that name is deliberately repeated at different
sites. The consumer fields include source metadata and the original point's sampling policy.
The reference contains plant IDs, canonical names and units, naming variations, rename history,
and the hold-out site. See the [version 1 naming convention](../../docs/architecture/tag-naming-convention.md).
