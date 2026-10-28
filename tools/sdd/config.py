"""Settings of the harness: where each file it reads or writes lives.

Read once into an immutable `Settings` object and passed to the composition root (principles.md,
"configuration"). All paths are repository-relative with forward slashes; `Settings.path` turns
one into an absolute `Path`. Changing a location here is a governed change (it moves the rules).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sdd.domain.errors import SddError


@dataclass(frozen=True)
class Settings:
    """Locations used by the harness.

    Attributes:
        root: absolute repository root.
        specs_dir: folder of the dossiers.
        requirements_file: the RT catalogue.
        team_file: who approves gates.
        templates_dir: artifact templates.
        checks_file: the G5 quality suite.
        logos_file: official logos for diagrams.
        decisions_dir: the ADRs.
        strict_logo_paths: documents where a diagram node without its logo is an error.
        lint_excluded: path prefixes skipped by the documentation lint (generated or templates).
    """

    root: Path
    specs_dir: str = "specs"
    requirements_file: str = "docs/requirements/rt-catalog.yaml"
    team_file: str = "harness/team.yaml"
    templates_dir: str = "harness/templates"
    checks_file: str = "harness/checks.yaml"
    logos_file: str = "docs/architecture/logos/registry.yaml"
    decisions_dir: str = "docs/architecture/decisions"
    strict_logo_paths: tuple[str, ...] = ("docs/architecture/", "README.md")
    lint_excluded: tuple[str, ...] = (".claude/", ".cursor/", ".github/", "harness/templates/")

    def path(self, relative: str) -> Path:
        """Return the absolute path of a repository-relative location.

        Args:
            relative: a path such as ``harness/team.yaml``.
        """
        return self.root / relative


def discover_root(start: Path) -> Path:
    """Find the repository root: the nearest folder holding `pyproject.toml` and `harness/`.

    Args:
        start: where to start looking (usually the current directory).

    Raises:
        SddError: when no such folder exists above `start`.
    """
    for folder in (start.resolve(), *start.resolve().parents):
        if (folder / "pyproject.toml").is_file() and (folder / "harness").is_dir():
            return folder
    raise SddError(f"no repository root (pyproject.toml + harness/) above {start}")
