# tssource · global plant data generator

Component of dossier [003](../../specs/003-tssource-skeleton-spike/spec.md) (child of umbrella
001). Card 01 delivers the package skeleton; card 02 adds `tssource bench`.

| Layer | Folder | Holds |
|---|---|---|
| domain | `domain/` | pure rules and `TssourceError` |
| application | `application/` | use cases, ports, immutable `Settings` |
| infrastructure | `infrastructure/` | adapters (numpy, pyarrow, files) |
| interfaces | `interfaces/cli/` | the Typer command line |
| root | `bootstrap.py` | the only place that wires |

```bash
poetry install --with tssource          # once
poetry run tssource --help              # run, bench, config, report, health
mkdir -p data/ts_source                 # the one writable folder of the container
docker compose up --build tssource      # idles, reported healthy
docker compose run --rm tssource --help
```

Settings come from `TSSOURCE_SEED`, `TSSOURCE_OUT`, `TSSOURCE_MODE`, `TSSOURCE_START`,
`TSSOURCE_END` and `TSSOURCE_SPEED_FACTOR`. Exit codes: 0 success, 1 not implemented or a
handled error, 2 usage, 3 benchmark floor missed (card 02).
