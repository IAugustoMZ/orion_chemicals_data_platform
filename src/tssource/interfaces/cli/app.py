"""The `tssource` command line: one Typer command per use case.

Exit codes are 0 for success, 1 for handled failures or unavailable commands, 2 for
usage errors and 3 when the benchmark misses its throughput floor.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from tssource.bootstrap import (
    build_catalogue_use_case,
    build_plant_use_case,
    build_settings,
    resolve_time_table,
    run_bench,
)
from tssource.domain.benchmark import Format
from tssource.domain.errors import TssourceError
from tssource.domain.time.resolution import TimeRangeError

app = typer.Typer(
    help=(
        "Global plant data generator. "
        "Exit codes: 0 success; 1 not implemented or handled error; 2 usage; 3 floor missed."
    ),
    no_args_is_help=True,
    add_completion=False,
)
plant_app = typer.Typer(
    help="Generate the private synthetic plant inventory.", no_args_is_help=True
)
app.add_typer(plant_app, name="plant")
catalog_app = typer.Typer(
    help="Export the tag catalogue and private reference.", no_args_is_help=True
)
app.add_typer(catalog_app, name="catalog")

BuildSeed = Annotated[int | None, typer.Option(min=0, help="Seed (default TSSOURCE_SEED).")]
BuildOutput = Annotated[Path | None, typer.Option(help="Output directory (default TSSOURCE_OUT).")]


@plant_app.command("build")
def plant_build(
    seed: BuildSeed = None,
    out: BuildOutput = None,
) -> None:
    """Write the private truth/plant.json fixture and print its path."""
    effective_seed, output_folder = _build_options(seed, out)
    try:
        path = build_plant_use_case().execute(effective_seed, output_folder)
    except TssourceError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(str(path))


@catalog_app.command("build")
def catalog_build(seed: BuildSeed = None, out: BuildOutput = None) -> None:
    """Publish the consumer catalogue and private reference, then print both paths."""
    effective_seed, output_folder = _build_options(seed, out)
    try:
        consumer, reference = build_catalogue_use_case(effective_seed).execute(output_folder)
    except TssourceError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(str(consumer))
    typer.echo(str(reference))


def _build_options(seed: int | None, out: Path | None) -> tuple[int, Path]:
    """Resolve shared build defaults and translate invalid settings into usage errors."""
    try:
        settings = build_settings()
    except TssourceError as error:
        raise typer.BadParameter(str(error)) from error
    effective_seed = settings.seed if seed is None else seed
    if effective_seed < 0:
        raise typer.BadParameter("TSSOURCE_SEED must be nonnegative.")
    return effective_seed, settings.output_folder if out is None else out


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
    seconds: Annotated[
        int, typer.Option(min=1, max=3600, help="Wall-clock seconds to run (1-3600).")
    ] = 60,
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


@app.command("time-table")
def time_table(
    site: Annotated[str, typer.Option(help="Declared site code.")],
    requested_date: Annotated[str, typer.Option("--date", help="ISO date (YYYY-MM-DD).")],
) -> None:
    """Print a 24-hour civil-time resolution table for one fictional site and date."""
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", requested_date):
            raise ValueError("expected YYYY-MM-DD")
        parsed_date = date.fromisoformat(requested_date)
    except ValueError as error:
        raise typer.BadParameter(
            f"Invalid date {requested_date} for {site}. Use a valid YYYY-MM-DD date."
        ) from error
    try:
        rows = resolve_time_table(site, parsed_date)
    except TimeRangeError as error:
        raise typer.BadParameter(
            f"The date {requested_date} is outside the supported UTC range for {site}. "
            "Choose a date farther from the calendar boundary."
        ) from error
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo("local | resolution | offsets | utc candidates")
    for row in rows:
        candidates = ", ".join(
            candidate.isoformat().replace("+00:00", "Z") for candidate in row.candidates
        )
        offsets = ", ".join(_format_offset(offset) for offset in row.offsets)
        typer.echo(f"{row.requested_local:%H:%M} | {row.status.value} | {offsets} | {candidates}")


def _format_offset(offset: object) -> str:
    """Render the adapter-provided offset without allowing the interface to resolve zones."""
    return str(offset)


def main() -> None:
    """Run the command line (the `tssource` console script)."""
    try:
        app()
    except TssourceError as error:
        typer.echo(f"error: {error}", err=True)
        raise SystemExit(1) from error
