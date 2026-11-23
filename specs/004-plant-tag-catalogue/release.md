# Release and learnings · 004 · Plant and tag catalogue

> **Phase 7 · Release & Learn**, closed by **G7 · Results validated** (both of us approve).
> How to fill this file: [lifecycle, phase 7](../../harness/lifecycle.md#phase-7-release-and-learn).

## Release

| Item | Result |
|---|---|
| Source | The initial release followed PR #36 at `648010d`. The final release followed the renewed validation in PR #39 at `fd412eeecf086c0ec2ef633e4dc4271b4dabc66f` on 2026-11-23. |
| Local service | Rebuilt and restarted Docker Compose `tssource`. Compose reported it healthy and the direct health command exited 0. |
| Image | `orion/tssource:local`, final image ID `sha256:41a1081f56a7edc10720958f2a524d4ca769b476f4b5175177b4945921c6f026`. |
| Data | The first probe used disposable files on container `/tmp`. After provisioning the host bind mount, both installed commands wrote the seed-42 artifacts to their default locations. The files survived container recreation. No migration was required. |

```bash
docker compose up -d --build --wait --wait-timeout 90 tssource
docker compose ps tssource
docker compose exec -T tssource tssource health
docker image inspect --format '{{.Id}}' orion/tssource:local
docker compose logs --no-color --tail 20 tssource
```

## Observation

The idle service emitted no logs in the observed window. A Python probe inside the running
container invoked the installed `tssource plant build` and `tssource catalog build` commands
with an explicit seed and destination. It measured command wall time, read the JSON and
Parquet files, and checked file contents, modes, schemas and relationships. All six fixture
commands exited 0, printed their intended paths and emitted empty stderr.

| Run | Seed | Plant build | Catalogue build |
|---|---:|---:|---:|
| Initial | 42 | 0.779 s | 0.936 s |
| Repeat in a fresh directory | 42 | 0.987 s | 0.820 s |
| Alternate | 101 | 0.838 s | 0.811 s |

These times include CLI startup in the local container. The PRD baseline had no plant-derived
fixture, so the observations establish a local baseline for this workflow.

The seed-42 plant JSON was 1,099,875 bytes. The consumer and reference files were 26,387 and
212,567 bytes respectively. All files were schema version 1 and had mode `0600`. With an
existing file deliberately passed as `--out`, the catalogue CLI exited 1, printed nothing
to stdout and emitted only `error: could not stage tags.parquet`. The existing file was intact.

The default bind mount was read-write, but its empty directory was owned by root with
mode `0755`. The command runs as UID 10001. I provisioned only the bind root for UID and
GID 10001 using a one-shot container with `CAP_CHOWN`, no network, and a read-only root
filesystem. The long-running service continued to run as UID 10001 with all capabilities
dropped. [Provisioning instructions](../../src/tssource/README.md#persistent-docker-output)

```bash
docker compose exec -T tssource test -w /data/ts_source
docker compose exec -T tssource tssource plant build --seed 42
docker compose exec -T tssource tssource catalog build --seed 42
docker compose up -d --no-build --force-recreate --wait --wait-timeout 60 tssource
```

Both build commands ran twice without an explicit `--out`. All three SHA-256 checksums
matched on the repeat run and again after recreating the service. The files were also
present under the host checkout's git-ignored `data/ts_source` tree with mode `0600`.
After the final image rebuild recreated the container, all three persisted checksums matched
before and after another pair of default-output builds.

With these files present, the original documentation build tried to read the Parquet catalogue
as a site asset and failed on its owner-only permissions. Corrective card
[PBI-004-05](backlog.md#pbi-004-05-keep-generated-fixtures-out-of-the-documentation-site)
excluded the fixture and local draft trees. On the final release commit,
`poetry run mkdocs build --strict --quiet --site-dir <isolated-site>` passed with the
real files present. The site retained its home and deployment pages and omitted both
local trees. [Validation record](validation.md#functional-validation)

| Artifact | SHA-256 |
|---|---|
| `truth/plant.json` | `2faf71c46f4fe80399ebaed19c9ccfbe802fcbcf3ab5dbb141227c6d1ff47a54` |
| `catalog/tags.parquet` | `c83dea2d6aa37a2680b0df4abf4603c1e4d83b9eb6c78c4a1e9c3b0e4ad7e55b` |
| `truth/tag_key.parquet` | `fda743acc519f66285e1e1006e366f1660bc8a24e6a1f8538ce8e2406250abb9` |

## Feedback

The release walkthrough used the installed commands as a fixture consumer. Explicit seeds
and an explicit destination made the artifacts straightforward to reproduce. The consumer
file could be read on its own, while the private reference supported the join and metadata
checks. During G7 review, the repository owner required persistent output on the default
bind mount before accepting the release. The ownership fix and recreate test above address
that feedback.

## Results against the goals

| PRD goal | Result | Evidence |
|---|---|---|
| Reproduce a plant | Met | 2,050 points across Brazil (700), US Gulf Coast (450), Belgium (350), China (350) and India (200). The smallest equipment class had 190 points. All 186 loops resolved three distinct roles within their area. All three files matched byte-for-byte across two seed-42 runs. Seed 101 produced disjoint equipment and instrument IDs. |
| Exercise identity matching | Met | 1,230 convention, 512 dialect and 308 ad hoc names (60.0%, 25.0% and 15.0% rounded). All 2,050 unique canonical names round-tripped. Each declared variation appeared on at least 20 points. Fifteen names were shared across sites, with distinct equipment in each collision. All 2,050 source and name keys linked one-to-one to the reference and to the matching plant instruments. |
| Declare sizing inputs | Met | Catalogue counts matched the plant inventory for every site and scan class. The counts at 1, 5, 10, 30, 60, 300 and 900 seconds were 186, 186, 186, 391, 224, 205 and 186. All 391 report-by-exception and 95 lab points had an unset interval. |
| Preserve metadata variation and reference separation | Met | 103 descriptors were empty and 103 reported units differed from the canonical unit (5.02% each). The consumer file matched its eight-column allowlist. The hold-out designation appeared only in the private reference and covered one site. |

## Learnings

Source-scoped names preserve meaningful collisions while giving consumers a stable join key.
An unset interval carries useful information for later completeness checks. The release probe
also showed why health and command execution both need checking. A deployment preflight
now documents the write check for the default output directory.

## Next items

- Apply the documented bind mount provisioning and write check when setting up a new checkout.
- Use the measured counts, scan classes and file sizes as inputs to a separate capacity worksheet and
  benchmark. Keep projections separate from container measurements.
