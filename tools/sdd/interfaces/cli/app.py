"""The `sdd` command line: one Typer command per use case.

Interfaces layer. Each command builds the harness through the composition root, calls one use
case and prints the result. Typed `SddError`s become a one-line message and exit code 2; error
findings become exit code 1. Run ``poetry run sdd --help`` for the list.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from sdd.application.use_cases.create_dossier import NewDossier
from sdd.bootstrap import Harness, build_harness
from sdd.config import Settings, discover_root
from sdd.domain.dossier import DossierKind
from sdd.domain.errors import GateNotReadyError, SddError, UnknownRequirementError
from sdd.domain.findings import has_errors
from sdd.domain.gates import parse_gate_id
from sdd.interfaces.cli import presenters

app = typer.Typer(
    help="Spec-driven development harness: dossiers, gates, approvals and checks.",
    no_args_is_help=True,
    add_completion=False,
)


def _harness() -> Harness:
    """Build the harness for the repository that contains the current directory."""
    return build_harness(Settings(discover_root(Path.cwd())))


def _run(action: Callable[[Harness], int | None]) -> None:
    """Run a command body, mapping typed errors to messages and exit codes.

    Args:
        action: the command body; returns an exit code or None for success.
    """
    try:
        code = action(_harness())
    except GateNotReadyError as error:
        typer.echo("Not ready for approval:", err=True)
        for problem in error.problems:
            typer.echo(f"  - {problem}", err=True)
        raise typer.Exit(2) from error
    except SddError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(2) from error
    raise typer.Exit(code or 0)


def _sync_quietly(harness: Harness) -> None:
    """Regenerate the derived documents after a change of the dossiers.

    Args:
        harness: the wired harness.
    """
    result = harness.sync.execute(write=True)
    for path in result.changed:
        typer.echo(f"  updated {path}")


@app.command()
def status(
    dossier_id: Annotated[str | None, typer.Argument(help="Dossier id; all when omitted.")] = None,
) -> None:
    """Show where each spec is: the state of its eight gates and the next step."""

    def body(harness: Harness) -> None:
        """Print one or every report."""
        reports = (harness.evaluate.one(dossier_id),) if dossier_id else harness.evaluate.all()
        if not reports:
            typer.echo('No spec yet. Start one with: poetry run sdd new "Title" --slug ...')
        for report in reports:
            typer.echo("\n".join(presenters.report_lines(report)) + "\n")

    _run(body)


@app.command()
def new(
    title: Annotated[str, typer.Argument(help="Human title of the work.")],
    slug: Annotated[str, typer.Option(help="kebab-case short name, e.g. source-contracts.")],
    rt: Annotated[
        list[str] | None, typer.Option("--rt", help="An RT served (repeat; none = outside RTs).")
    ] = None,
    kind: Annotated[DossierKind, typer.Option(help="feature or enabler.")] = DossierKind.FEATURE,
    rationale: Annotated[
        str, typer.Option(help="Why (mandatory for enablers and work outside the RTs).")
    ] = "",
) -> None:
    """Create a new dossier specs/<id>-<slug>/ from the templates."""

    def body(harness: Harness) -> None:
        """Create the dossier and refresh the generated documents."""
        requirements = tuple(dict.fromkeys(r.strip().upper() for r in rt or ()))
        dossier = harness.create.execute(NewDossier(title, slug, kind, requirements, rationale))
        typer.echo(f"Created specs/{dossier.folder_name}/ ; work on branch {dossier.branch_name}")
        typer.echo(f"  git switch -c {dossier.branch_name}")
        _sync_quietly(harness)

    _run(body)


@app.command()
def approve(
    dossier_id: Annotated[str, typer.Argument(help="Dossier id, e.g. 001.")],
    gate: Annotated[str, typer.Argument(help="Human gate: G1, G2, G3, G4, G6 or G7.")],
    member: Annotated[str, typer.Option("--as", help="Your id in harness/team.yaml.")],
    note: Annotated[str, typer.Option(help="Optional remark kept with the approval.")] = "",
) -> None:
    """Approve a human gate (people only: asks for confirmation at the terminal)."""

    def body(harness: Harness) -> None:
        """Record the approval and refresh the generated documents."""
        result = harness.approve.execute(dossier_id, parse_gate_id(gate), member, note)
        typer.echo(f"{result.gate.id}: {result.state.value} ({result.detail})")
        _sync_quietly(harness)

    _run(body)


@app.command()
def verify(dossier_id: Annotated[str, typer.Argument(help="Dossier id, e.g. 001.")]) -> None:
    """Run the deterministic quality suite (gate G5) and record the result."""

    def body(harness: Harness) -> int:
        """Run the suite, print progress, and return 1 when it failed."""
        verification = harness.verify.execute(
            dossier_id, lambda c, o: typer.echo(presenters.check_progress(c, o))
        )
        typer.echo(presenters.verification_line(verification))
        _sync_quietly(harness)
        return 0 if verification.passed else 1

    _run(body)


@app.command()
def check() -> None:
    """Check the repository against the harness (dossiers, docs, generated files)."""

    def body(harness: Harness) -> int:
        """Print the findings and return 1 when any is an error."""
        findings = harness.check.execute()
        for line in presenters.finding_lines(findings):
            typer.echo(line)
        typer.echo(f"sdd check: {len(findings)} finding(s)")
        return 1 if has_errors(findings) else 0

    _run(body)


@app.command()
def sync(
    check_only: Annotated[bool, typer.Option("--check", help="Only report drift.")] = False,
) -> None:
    """Regenerate README status, specs index, traceability matrix and tool adapters."""

    def body(harness: Harness) -> int:
        """Write (or only report) the generated files; return 1 on drift or problems."""
        result = harness.sync.execute(write=not check_only)
        verb = "out of date" if check_only else "updated"
        for path in result.changed:
            typer.echo(f"{verb}: {path}")
        for path in result.removed:
            typer.echo(f"{'orphan' if check_only else 'removed'}: {path}")
        for line in presenters.finding_lines(result.problems):
            typer.echo(line)
        drift = bool(result.changed or result.removed)
        return 1 if result.problems or (check_only and drift) else 0

    _run(body)


@app.command("guard-commit")
def guard_commit(
    files: Annotated[list[str] | None, typer.Argument(help="Staged files.")] = None,
) -> None:
    """Refuse governed changes outside an approved spec branch (used by pre-commit)."""

    def body(harness: Harness) -> int:
        """Print the guard's findings and return 1 when the commit must stop."""
        findings = harness.guard.execute(files or [])
        for line in presenters.finding_lines(findings):
            typer.echo(line)
        return 1 if has_errors(findings) else 0

    _run(body)


@app.command("rt")
def show_requirements(
    ids: Annotated[list[str] | None, typer.Argument(help="RT ids; all when omitted.")] = None,
) -> None:
    """Show technical requirements from the catalogue (what must hold, how to verify)."""

    def body(harness: Harness) -> None:
        """Print the requested requirements."""
        catalog = harness.requirements.all()
        wanted = [i.strip().upper() for i in ids] if ids else sorted(catalog)
        unknown = [i for i in wanted if i not in catalog]
        if unknown:
            raise UnknownRequirementError(f"not in the catalogue: {', '.join(unknown)}")
        for rt_id in wanted:
            typer.echo("\n".join(presenters.requirement_lines(catalog[rt_id])))

    _run(body)


def main() -> None:
    """Run the command line (the `sdd` console script)."""
    app()
