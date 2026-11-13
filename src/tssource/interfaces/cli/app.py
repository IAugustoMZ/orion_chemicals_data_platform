"""The `tssource` command line: one Typer command per use case.

Interfaces layer. Five commands exist: ``run``, ``config`` and ``report`` say "not implemented
yet" (exit 1) until their cards arrive; ``bench`` (card 02) measures throughput; ``health``
checks that the settings are readable (exit 0). Exit codes: 0 success, 1 not implemented or a
handled ``TssourceError``, 2 usage error (Typer), 3 benchmark floor missed. Errors are one line,
never a stack trace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from tssource.bootstrap import build_settings, run_bench
from tssource.domain.benchmark import Format
from tssource.domain.errors import TssourceError

app = typer.Typer(
    help=(
        "Global plant data generator. "
        "Exit codes: 0 success; 1 not implemented or handled error; 2 usage; 3 floor missed."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def _not_implemented(command: str) -> None:
    """Print the one-line message on stderr and exit with code 1."""
    typer.echo(f"{command}: not implemented yet", err=True)
    raise typer.Exit(code=1)


@app.command()
def run() -> None:
    """Generate plant data (not implemented yet)."""
    _not_implemented("run")


@app.command()
def bench(
    seconds: Annotated[int, typer.Option(min=1, help="Wall-clock seconds to run.")] = 60,
    seed: Annotated[int | None, typer.Option(help="Random seed (default TSSOURCE_SEED).")] = None,
    fmt: Annotated[Format, typer.Option("--format", help="Serialiser to measure.")] = (
        Format.JSONL_GZIP
    ),
    out: Annotated[
        Path | None, typer.Option(help="Folder for bench.json (default TSSOURCE_OUT).")
    ] = None,
) -> None:
    """Measure sustained events/s as a per-second distribution; exit 3 below the floor."""
    result = run_bench(seconds=seconds, fmt=fmt, seed=seed, out=out)
    folder = build_settings().output_folder if out is None else out
    folder.mkdir(parents=True, exist_ok=True)
    document = json.dumps(result.as_json(), indent=2)
    (folder / "bench.json").write_text(document + "\n", encoding="utf-8")
    typer.echo(document)
    if not result.floor_held:
        typer.echo(
            f"bench: mean {result.distribution.mean:,.0f} events/s is below the floor of "
            f"{result.floor:,}; bottleneck: {result.bottleneck.value}",
            err=True,
        )
        raise typer.Exit(code=3)


@app.command()
def config() -> None:
    """Show the effective settings (not implemented yet)."""
    _not_implemented("config")


@app.command()
def report() -> None:
    """Report on generated data (not implemented yet)."""
    _not_implemented("report")


@app.command()
def health() -> None:
    """Exit 0 when the settings can be read; used by the container healthcheck."""
    build_settings()


def main() -> None:
    """Run the command line (the `tssource` console script)."""
    try:
        app()
    except TssourceError as error:
        typer.echo(f"error: {error}", err=True)
        raise SystemExit(1) from error
