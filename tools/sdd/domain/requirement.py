"""Technical requirements (RT01-RT42) as the harness sees them.

Domain layer. The requirements come from the Orion Chemicals catalogue
(`docs/requirements/rt-catalog.yaml`, transcribed from the PDF). Every dossier cites the RTs it
serves; gate G0 fails when a citation is unknown, which keeps every piece of work traceable to a
requirement (Constitution, article I).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

RT_ID_PATTERN = re.compile(r"\bRT\d{2}\b")
"""Matches an RT identifier anywhere in a text (used to find citations in Markdown)."""


class RequirementPhase(StrEnum):
    """When a requirement must hold, as classified by the catalogue."""

    PROTOTYPE = "P"
    EXPANSION = "A"


@dataclass(frozen=True)
class Requirement:
    """One verifiable technical requirement.

    Attributes:
        id: "RTnn".
        category: section of the catalogue (integration, identity-quality, ...).
        phase: prototype (P) or operational expansion (A).
        priority: true when the catalogue asks to tackle it first.
        statement: what must hold, in English.
        verification: how we prove it holds (the catalogue's "forma de verificar").
    """

    id: str
    category: str
    phase: RequirementPhase
    priority: bool
    statement: str
    verification: str
