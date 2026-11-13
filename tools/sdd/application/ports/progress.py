"""Ports for the per-card flow: where progress is stored and how AC evidence is read.

Application layer. `ProgressRepository` hides the YAML file; `AcStatusReader` hides how the
tests are run, so the use cases can be tested with fakes and the test runner can change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from sdd.domain.item_progress import ItemProgress


class ProgressRepository(Protocol):
    """Load and save the `progress.yaml` of a dossier."""

    def load(self, dossier_id: str) -> ItemProgress | None:
        """Return the progress of the dossier, or None when it has no `progress.yaml`.

        Args:
            dossier_id: three-digit dossier id.
        """
        ...

    def save(self, dossier_id: str, progress: ItemProgress) -> None:
        """Write the progress of the dossier.

        Args:
            dossier_id: three-digit dossier id.
            progress: the full snapshot to store.
        """
        ...


class AcStatusReader(Protocol):
    """Tell which acceptance criteria are covered by a passing marked test."""

    def read(self) -> Mapping[str, bool]:
        """Run the marked tests.

        Returns:
            Marker id (``"PBI-002-02:AC1"``) to true when every test carrying it passed; an id
            with no test is absent.
        """
        ...
