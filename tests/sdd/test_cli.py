"""End-to-end tests of the `sdd` command line in a throwaway copy of the harness."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdd.interfaces.cli.app import app

REPO = Path(__file__).resolve().parents[2]
COPIED = (
    "harness/templates",
    "harness/team.yaml",
    "harness/checks.yaml",
    "docs/requirements/rt-catalog.yaml",
    "docs/architecture/logos/registry.yaml",
)
README = (
    "# Test\n<!-- sdd:status:start -->\n<!-- sdd:status:end -->\n"
    "<!-- sdd:coverage:start -->\n<!-- sdd:coverage:end -->\n"
)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for item in COPIED:
        source, target = REPO / item, tmp_path / item
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy(source, target)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 't'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(README, encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(*args: str):
    return CliRunner().invoke(app, list(args))


def test_new_status_rt_and_sync(repo):
    created = run("new", "Source contracts", "--slug", "source-contracts", "--rt", "rt02")
    assert created.exit_code == 0, created.output
    assert "spec/000-source-contracts" in created.output
    prd = (repo / "specs/000-source-contracts/prd.md").read_text(encoding="utf-8")
    assert "Each source shall have an integration contract" in prd
    status = run("status")
    assert "G1 Discover" in status.output and "pending" in status.output
    assert "[000 · Source contracts]" in (repo / "README.md").read_text(encoding="utf-8")
    assert run("sync", "--check").exit_code == 0
    shown = run("rt", "RT09")
    assert "never point to two pieces of equipment" in shown.output


def test_typed_errors_exit_with_2(repo):
    assert run("new", "X", "--slug", "x", "--rt", "RT99").exit_code == 2
    run("new", "X", "--slug", "x", "--rt", "RT01")
    refused = run("approve", "000", "G1", "--as", "mentor")
    assert refused.exit_code == 2
    assert "Not ready for approval" in refused.output or "interactive terminal" in refused.output
    assert run("status", "042").exit_code == 2


def test_guard_and_check(repo):
    run("new", "X", "--slug", "x", "--rt", "RT01")
    blocked = run("guard-commit", "tools/sdd/a.py")
    assert blocked.exit_code == 1 and "commit-guard" in blocked.output
    assert run("guard-commit", "docs/a.md").exit_code == 0
    checked = run("check")
    assert "sdd check:" in checked.output
