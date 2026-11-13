"""`lint-imports` refuses frameworks in the inner layers of `tssource` (B03)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

CONFIG = """\
[tool.importlinter]
root_packages = ["tssource"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "inner layers stay free of numpy, pyarrow and typer"
type = "forbidden"
source_modules = ["tssource.domain", "tssource.application"]
forbidden_modules = ["numpy", "pyarrow", "typer"]
"""
RUN = "from importlinter.cli import lint_imports_command; lint_imports_command()"


def _lint(tmp_path: Path, layer: str, body: str) -> subprocess.CompletedProcess[str]:
    """Build a tiny `tssource` package with one module in `layer` and lint it."""
    package = tmp_path / "tssource"
    for name in ("", "domain", "application"):
        (package / name).mkdir(parents=True, exist_ok=True)
        (package / name / "__init__.py").write_text('"""Fixture."""\n', encoding="utf-8")
    (package / layer / "sample.py").write_text(body, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(CONFIG, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            "-c",
            RUN,
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.ac("PBI-003-01:AC3")
@pytest.mark.parametrize("layer", ["domain", "application"])
@pytest.mark.parametrize("library", ["numpy", "pyarrow", "typer"])
def test_forbidden_import_fails(tmp_path: Path, layer: str, library: str) -> None:
    """An inner layer that imports a forbidden library breaks the contract."""
    assert _lint(tmp_path, layer, f"import {library}\n").returncode != 0


@pytest.mark.ac("PBI-003-01:AC3")
def test_clean_inner_layer_passes(tmp_path: Path) -> None:
    """The same package without the forbidden import passes."""
    assert _lint(tmp_path, "domain", "import json\n").returncode == 0
