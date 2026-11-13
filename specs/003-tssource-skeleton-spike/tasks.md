# Tasks · 003 · Generator skeleton and throughput spike

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. During the build, tick the
> boxes: ticking does not invalidate G4 (the digest ignores the box state), but rewording,
> adding or removing a task does, on purpose.

## Tasks

Card 01 · branch `feat/003-01-skeleton`

- [ ] T01 · Write failing tests `test_cli.py`, `test_compose_hardening.py`, `test_layers.py`, marked with the card's ACs *(SPEC-003-B01, B02, B03; plan step 1)*
- [ ] T02 · Add group `tssource` and extend ruff, mypy, pytest, coverage, import-linter, bandit; `poetry lock` *(B03; plan step 2)*
- [ ] T03 · Create the four layers, `TssourceError`, `Settings`, `bootstrap.py` and the Typer app *(B01; plan step 3)*
- [ ] T04 · Write `docker/tssource.Dockerfile`, the compose service and the `.gitignore` entry; build, confirm healthy *(B02; plan step 4)*
- [ ] T05 · Run `sdd item verify 003 01`, update `deployment.md` and READMEs, open the pull request and stop *(B01-B03; plan step 5)*

Card 02 · branch `feat/003-02-throughput-spike`

- [ ] T06 · Write failing `test_benchmark.py` with fakes: distribution maths, queue bound, exit 3 with the stage, determinism *(SPEC-003-B04 to B07; plan step 6)*
- [ ] T07 · Implement `Distribution` and `BenchResult` in the domain *(B04; plan step 7)*
- [ ] T08 · Implement `RunBenchmark` and the four ports in the application *(B05, B06; plan step 7)*
- [ ] T09 · Implement `NumpyBlockSource`, the three sinks, the probe and the clock *(B04, B07; plan step 7)*
- [ ] T10 · Wire `bench` in the CLI and `bootstrap.py`; exit 3 below the floor *(B04, B06; plan step 7)*
- [ ] T11 · Run the three 60 s measurements in the container; attach `bench.json` and the table; draft the writer ADR *(RT29, RT28; plan step 8)*
- [ ] T12 · Run `sdd item verify 003 02`, teaching guide, open the pull request and stop *(B04-B07; plan step 9)*

## Loop limits

The build agent runs `poetry run sdd verify 003` after each task. After **3** consecutive
failing verifications on the same task it stops and asks us
([AI control plane](../../harness/ai-control-plane.md#loop-limits-and-escalation)).

Default kept: the limit is 3 for this dossier, because every task is small.
