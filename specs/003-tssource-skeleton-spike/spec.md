# Execution specification · 003 · Generator skeleton and throughput spike
> **Phase 4 · Specify**, closed by **G4** (both approve spec, plan, tasks). Diagrams, classes and files live in [plan.md](plan.md); detail in the [backlog](backlog.md).
## Context collected
| Source | Where | What it contributed |
|---|---|---|
| RT28, RT29, RT01, RT36; PRD, backlog, approach; ADR-0007, 0019, 0023, 0024; `principles.md`, `security.md`; `pyproject.toml`, `compose.yaml`, `docker/docs.Dockerfile` | repo | goals, 25,000 events/s floor, layers, `tssource` group, hardening baseline |
## Behaviour
| ID | Behaviour (EARS) | RT | Backlog criteria |
|---|---|---|---|
| SPEC-003-B01 | When `tssource --help` runs, it shall list `run`, `bench`, `config`, `report`, `health` and exit 0; `run`, `config`, `report` (and `bench` until card 02) shall print "<command>: not implemented yet" and exit 1; `health` exits 0. | RT01 | PBI-003-01 AC1, AC4 |
| SPEC-003-B02 | The `tssource` service shall run read-only, without capabilities, with `no-new-privileges`, as user 10001 and with no published port. | RT01, RT36 | PBI-003-01 AC2 |
| SPEC-003-B03 | If `domain` or `application` imports `numpy`, `pyarrow` or `typer`, then `lint-imports` shall fail; the new files shall hold no credential (`detect-secrets` passes). | RT36 | PBI-003-01 AC3, AC5 |
| SPEC-003-B04 | When `tssource bench` ends, it shall write `bench.json` with mean, p50, p95, p99, minimum events/s, events, CPU seconds, peak memory, floor and bottleneck. | RT29, RT28 | PBI-003-02 AC1 |
| SPEC-003-B05 | While the benchmark runs, the writer queue depth shall never exceed its bound. | RT29 | PBI-003-02 AC2 |
| SPEC-003-B06 | If the mean rate over the run is below 25,000 events/s (minimum and p99 are only reported), then `bench` shall exit 3 and name the stage (`generation` or `writing`). | RT29 | PBI-003-02 AC3 |
| SPEC-003-B07 | When run twice with one seed, `bench` shall produce the same events. | RT28 | PBI-003-02 AC4 |
## Architecture impact
| Component | Change | Layer or place | Why |
|---|---|---|---|
| `tssource` package: `Settings`, `TssourceError`, composition root, Typer CLI | added | `src/tssource/` four layers | skeleton (card 01) |
| `RunBenchmark`, `Distribution`, `BenchResult`, ports, numpy source, three sinks, probe, clock | added | domain, application, infrastructure | spike (card 02) |
| service `tssource`, `docker/tssource.Dockerfile`, `data/` ignore; Poetry group `tssource` (`numpy`, `pyarrow`, `tzdata`) | added | compose, docker, `pyproject.toml` | hardened container; ADR-0019; before/after diagrams in [plan.md](plan.md#architecture-before-and-after) |
## Contracts and data
| Contract | Shape | Producer | Consumers | Versioning |
|---|---|---|---|---|
| CLI `tssource` | five commands; options `--seconds --seed --format --out`, env `TSSOURCE_<NAME>`; exit 0/1/2/3 | `tssource` | people, later cards | additive only |
| `bench.json` | `seed, format, seconds, events, events_per_second{mean,p50,p95,p99,min}, cpu_seconds, peak_memory_mb, floor, floor_held, bottleneck` | `bench` | mentor, 001 report card | `version: 1` field; names stable |
## Design
| Layer | Class or module | Responsibility (one reason to change) | Collaborators (ports) |
|---|---|---|---|
| domain, application | `Distribution`, `BenchResult`, `TssourceError`; `Settings`, `RunBenchmark` | pure percentiles; read once; two threads, bounded queue | `EventSource`, `EventSink`, `ResourceProbe`, `Clock` |
| infrastructure | `NumpyBlockSource`, `JsonlGzipSink`, `JsonlSink`, `ParquetSink`, probe, clock | one adapter per port | numpy, pyarrow, stdlib |
| interfaces / root | Typer `app`, `bootstrap.py` | parse input, map errors to exit codes; wire | use cases; patterns and SOLID in [plan.md](plan.md#design) |
## Security and threat model
| Threat (STRIDE) | Mitigation | Verified by |
|---|---|---|
| Tampering, Elevation, Disclosure: writable container, extra privileges, credentials in code or image | read-only root, `cap_drop`, `no-new-privileges`, non-root, one bind; no credential used; `detect-secrets` | B02 test, B03 |
| Denial of service: runaway benchmark fills disk or memory | `--seconds` bound, scratch under `data/ts_source`, queue bound | B05 |
## Validation plan
| Behaviour or RT | Level | Evidence |
|---|---|---|
| B01-B07; RT29, RT28 | unit and integration with fakes, compose parsed as YAML; measurement by us | tests named in each card; three real 60 s container runs, `bench.json` files in the PR |
## Architecture decisions
| ADR | Decision | Status | Refines or supersedes |
|---|---|---|---|
| 0019 (package, group) and 0027 (per-second distribution, bounded queue, exit 3) | second package; benchmark method | Proposed | ADR-0005, 0007; ADR-0019 |
## Documentation impact
`deployment.md` (service and diagram), `README.md`, a `src/tssource/README.md`, the teaching guide, then `sdd sync`.
## Out of scope
Signal realism, final file layout, real-time writer, heartbeat, delay measurement, Kafka/HTTP, the sizing report (001 card 21).
