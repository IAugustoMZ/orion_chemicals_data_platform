"""`sdd`: the command-line tool that runs our spec-driven development (SDD) harness.

The harness is described for people in `harness/how-it-works.md`; this package is the part of it
that a machine can enforce: it creates spec dossiers, evaluates the eight gates (G0-G7), records
our approvals, runs the deterministic quality suite (gate G5), guards commits and regenerates the
documents derived from the dossiers (README status, traceability matrix, tool adapters).

The package follows clean architecture (ADR-0007), and `lint-imports` enforces the direction of
every import:

    interfaces  ->  bootstrap  ->  infrastructure  ->  application  ->  domain

* `domain`         the lifecycle's concepts (gates, dossiers, approvals, team), pure Python.
* `application`    use cases and the ports (Protocols) they need from the outside world.
* `infrastructure` adapters that implement the ports with YAML files, git and subprocesses.
* `bootstrap`      the composition root: the only place where adapters are instantiated.
* `interfaces`     the Typer command line that people and agents call.
"""
