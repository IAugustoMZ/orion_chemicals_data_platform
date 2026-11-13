"""The files of the `tssource` skeleton hold no credential (B03, RT36)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.ac("PBI-003-01:AC5")
def test_detect_secrets_passes_on_the_new_files() -> None:
    """`detect-secrets-hook` finds nothing new in the package, image and compose file."""
    files = [
        *(str(path) for path in (ROOT / "src" / "tssource").rglob("*") if path.is_file()),
        str(ROOT / "docker" / "tssource.Dockerfile"),
        str(ROOT / "compose.yaml"),
    ]
    result = subprocess.run(
        ["detect-secrets-hook", "--baseline", str(ROOT / ".secrets.baseline"), *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout
