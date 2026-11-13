"""The `tssource` command line: one Typer command per use case.

Interfaces layer. Five commands exist from card 01: ``run``, ``bench``, ``config`` and
``report`` say "not implemented yet" (exit 1) until their cards arrive; ``health`` checks that
the settings are readable (exit 0). Exit codes: 0 success, 1 not implemented or a handled
``TssourceError``, 2 usage error (Typer), 3 benchmark floor missed (card 02). Errors are one
line, never a stack trace.
"""

from __future__ import annotations

import typer

from tssource.bootstrap import build_settings
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
def bench() -> None:
    """Measure throughput (not implemented yet)."""
    _not_implemented("bench")


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
