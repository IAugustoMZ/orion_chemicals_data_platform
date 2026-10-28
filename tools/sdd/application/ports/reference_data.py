"""Ports for the read-only reference data of the harness.

Application layer. Four small Protocols, one per file of `harness/` or `docs/` that the use
cases read: the requirement catalogue, the team, the quality suite and the logo registry.
They are separate so that a use case depends only on the data it actually uses.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from sdd.domain.quality import QualityCheck
from sdd.domain.requirement import Requirement
from sdd.domain.team import Team


@dataclass(frozen=True)
class Logo:
    """The official logo of a tool, for Mermaid diagrams (harness/documentation-standard.md).

    Attributes:
        name: the tool's name as written in diagrams, e.g. "PostgreSQL".
        aliases: other spellings that also mean this tool, e.g. ("Postgres",).
        url: URL of the official logo (simpleicons or devicon CDN).
    """

    name: str
    aliases: tuple[str, ...]
    url: str


class RequirementCatalog(Protocol):
    """The RT01-RT42 catalogue."""

    def all(self) -> Mapping[str, Requirement]:
        """Return every requirement by id."""
        ...

    def categories(self) -> Mapping[str, str]:
        """Return the catalogue's categories, key -> title, in document order."""
        ...


class TeamDirectory(Protocol):
    """Who approves gates (`harness/team.yaml`)."""

    def load(self) -> Team:
        """Return the team.

        Raises:
            InvalidTeamError: when the file is malformed.
        """
        ...


class QualityCheckCatalog(Protocol):
    """The deterministic suite of gate G5 (`harness/checks.yaml`)."""

    def all(self) -> tuple[QualityCheck, ...]:
        """Return the checks in the order they must run."""
        ...


class LogoRegistry(Protocol):
    """Official logos per tool (`docs/architecture/logos/registry.yaml`)."""

    def logos(self) -> tuple[Logo, ...]:
        """Return every registered logo."""
        ...
