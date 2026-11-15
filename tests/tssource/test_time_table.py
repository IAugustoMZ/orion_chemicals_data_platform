"""Acceptance tests for the civil-time diagnostic command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tssource.interfaces.cli.app import app

_RUNNER = CliRunner()


@pytest.mark.ac("PBI-001-05:AC6")
def test_time_table_prints_twenty_four_rows_and_gap_resolution() -> None:
    """The command keeps the skipped local hour visible beside its resolved UTC instant."""
    result = _RUNNER.invoke(app, ["time-table", "--site", "us-gulf-coast", "--date", "2024-03-10"])
    assert result.exit_code == 0
    assert len([line for line in result.output.splitlines() if " | " in line]) == 25
    assert "02:00 | gap" in result.output
    assert "2024-03-10T08:00:00Z" in result.output


@pytest.mark.ac("PBI-001-05:AC6")
def test_time_table_rejects_an_unknown_site() -> None:
    """Bad CLI input exits with Typer's usage code and never exposes a traceback."""
    result = _RUNNER.invoke(app, ["time-table", "--site", "bad", "--date", "2024-03-10"])
    assert result.exit_code == 2
    assert "Traceback" not in result.output
