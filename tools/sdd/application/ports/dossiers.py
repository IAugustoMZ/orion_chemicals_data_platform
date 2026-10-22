"""Port for storing dossiers (the `specs/<id>-<slug>/` folders).

Application layer. The use cases never touch the file system directly; they ask a
`DossierRepository`, which the infrastructure layer implements with YAML and Markdown files.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from sdd.domain.dossier import Dossier


class DossierRepository(Protocol):
    """Load, save and create dossiers and read their artifacts."""

    def ids(self) -> tuple[str, ...]:
        """Return the ids of every existing dossier, sorted ascending."""
        ...

    def load(self, dossier_id: str) -> Dossier:
        """Return the dossier with this id.

        Raises:
            DossierNotFoundError: when it does not exist.
            InvalidDossierError: when its metadata is malformed.
        """
        ...

    def save(self, dossier: Dossier) -> None:
        """Persist the dossier's metadata (`dossier.yaml`), leaving the artifacts untouched."""
        ...

    def create(self, dossier: Dossier, artifacts: Mapping[str, str]) -> None:
        """Create the dossier folder with its metadata and initial artifacts.

        Args:
            dossier: the new dossier; its folder must not exist yet.
            artifacts: file name -> initial content (rendered templates).
        """
        ...

    def read_artifact(self, dossier: Dossier, name: str) -> str | None:
        """Return the content of an artifact, or None when the file does not exist."""
        ...

    def location(self, dossier: Dossier) -> str:
        """Return the repository-relative folder of the dossier, for messages."""
        ...
