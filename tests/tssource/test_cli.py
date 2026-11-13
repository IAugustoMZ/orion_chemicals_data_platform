"""The `tssource` command line: its commands, exit codes and one-line messages (B01)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tssource.interfaces.cli.app import app

runner = CliRunner()
COMMANDS = ("run", "bench", "config", "report", "health")


@pytest.mark.ac("PBI-003-01:AC1")
def test_help_lists_the_five_commands_and_exits_zero() -> None:
    """`--help` names every command and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert all(command in result.output for command in COMMANDS)


@pytest.mark.ac("PBI-003-01:AC4")
@pytest.mark.parametrize("command", ["run", "config", "report"])
def test_unbuilt_commands_say_not_implemented_and_exit_one(command: str) -> None:
    """Every command that is not built yet prints one line and exits 1."""
    result = runner.invoke(app, [command])
    assert result.exit_code == 1
    assert f"{command}: not implemented yet" in result.output
    assert "Traceback" not in result.output


@pytest.mark.ac("PBI-003-01:AC1")
def test_health_exits_zero() -> None:
    """`health` succeeds so the container healthcheck can use it."""
    assert runner.invoke(app, ["health"]).exit_code == 0
