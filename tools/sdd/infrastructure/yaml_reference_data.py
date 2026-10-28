"""Adapters of the reference-data ports, each reading one YAML file.

Infrastructure layer. Four small classes, one per port (`RequirementCatalog`, `TeamDirectory`,
`QualityCheckCatalog`, `LogoRegistry`). Each file is parsed lazily, once, with `yaml.safe_load`
(never `yaml.load`: a YAML file must not be able to construct arbitrary Python objects).
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml

from sdd.application.ports.reference_data import Logo
from sdd.domain.errors import InvalidTeamError
from sdd.domain.quality import QualityCheck
from sdd.domain.requirement import Requirement, RequirementPhase
from sdd.domain.team import ApprovalPolicy, Team, TeamMember


def _load(path: Path) -> Any:
    """Parse a YAML file safely.

    Args:
        path: absolute path of the file.
    """
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class YamlRequirementCatalog:
    """The RT catalogue in `docs/requirements/rt-catalog.yaml`."""

    def __init__(self, path: Path) -> None:
        """Remember the file.

        Args:
            path: absolute path of the catalogue.
        """
        self._path = path

    @cached_property
    def _data(self) -> dict[str, Any]:
        """Return the parsed catalogue (read once)."""
        data: dict[str, Any] = _load(self._path)
        return data

    def all(self) -> Mapping[str, Requirement]:
        """Return every requirement by id."""
        return {
            str(entry["id"]): Requirement(
                id=str(entry["id"]),
                category=str(entry["category"]),
                phase=RequirementPhase(entry["phase"]),
                priority=bool(entry.get("priority", False)),
                statement=" ".join(str(entry["statement"]).split()),
                verification=" ".join(str(entry["verification"]).split()),
            )
            for entry in self._data["requirements"]
        }

    def categories(self) -> Mapping[str, str]:
        """Return the categories, key -> title, in document order."""
        return {str(k): str(v) for k, v in self._data["categories"].items()}


class YamlTeamDirectory:
    """The team in `harness/team.yaml`."""

    def __init__(self, path: Path) -> None:
        """Remember the file.

        Args:
            path: absolute path of the team file.
        """
        self._path = path

    def load(self) -> Team:
        """Return the team.

        Raises:
            InvalidTeamError: when the file is malformed.
        """
        try:
            data = _load(self._path)
            members = tuple(
                TeamMember(str(m["id"]), str(m["name"]), str(m.get("role", "")))
                for m in data["members"]
            )
            return Team(members, ApprovalPolicy(data.get("approval_policy", "all")))
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as error:
            raise InvalidTeamError(f"harness/team.yaml is malformed: {error}") from error


class YamlQualityCheckCatalog:
    """The G5 suite in `harness/checks.yaml`."""

    def __init__(self, path: Path) -> None:
        """Remember the file.

        Args:
            path: absolute path of the suite file.
        """
        self._path = path

    def all(self) -> tuple[QualityCheck, ...]:
        """Return the checks in file order."""
        return tuple(
            QualityCheck(
                id=str(c["id"]),
                title=str(c["title"]),
                command=tuple(str(part) for part in c["command"]),
                pass_files=bool(c.get("pass_files", False)),
            )
            for c in _load(self._path)["checks"]
        )


class YamlLogoRegistry:
    """The official logos in `docs/architecture/logos/registry.yaml`."""

    def __init__(self, path: Path) -> None:
        """Remember the file.

        Args:
            path: absolute path of the registry.
        """
        self._path = path

    def logos(self) -> tuple[Logo, ...]:
        """Return every registered logo."""
        return tuple(
            Logo(str(e["name"]), tuple(str(a) for a in e.get("aliases") or ()), str(e["url"]))
            for e in _load(self._path)["logos"]
        )
