"""The dossier: everything about one spec, from the first idea to the release.

Domain layer. A dossier is a folder `specs/<id>-<slug>/` holding one Markdown artifact per phase
plus `dossier.yaml` (this class). It is the aggregate root of the harness: approvals and the G5
verification belong to it and are only changed through its methods, which return a *new* dossier
(immutability keeps the history explicit and the tests simple).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from enum import StrEnum

from sdd.domain.approval import Approval, Verification
from sdd.domain.errors import InvalidDossierError
from sdd.domain.gates import GateId

_ID = re.compile(r"^\d{3}$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class DossierKind(StrEnum):
    """Why a dossier exists."""

    FEATURE = "feature"
    """Delivers platform behaviour; cites the RTs it satisfies or, when none applies, is
    *outside the catalogue* and states its rationale."""

    ENABLER = "enabler"
    """Builds tooling or foundations (like the harness itself); may cite RTs it *supports*,
    and must state its rationale."""


@dataclass(frozen=True)
class Dossier:
    """Metadata and gate evidence of one spec.

    Attributes:
        id: three digits, assigned in creation order ("000", "001", ...), never reused.
        slug: kebab-case short name; folder and branch names are derived from it.
        title: human title.
        kind: feature or enabler.
        requirements: RT ids the dossier serves, in the order they were cited.
        rationale: why the work is worth doing (mandatory for enablers and for features
            outside the catalogue).
        created: creation date.
        approvals: approvals per human gate; at most one per member per gate (the latest).
        verification: the latest G5 verification, if the suite was ever run.
    """

    id: str
    slug: str
    title: str
    kind: DossierKind
    requirements: tuple[str, ...]
    rationale: str
    created: date
    approvals: Mapping[GateId, tuple[Approval, ...]] = field(default_factory=dict)
    verification: Verification | None = None

    def __post_init__(self) -> None:
        """Validate the identity fields, from which paths and branch names are derived.

        Raises:
            InvalidDossierError: when the id, slug or title is malformed.
        """
        if not _ID.match(self.id):
            raise InvalidDossierError(f"dossier id {self.id!r} must be three digits")
        if not _SLUG.match(self.slug):
            raise InvalidDossierError(f"slug {self.slug!r} must be kebab-case (a-z, 0-9, -)")
        if not self.title.strip():
            raise InvalidDossierError("a dossier needs a title")

    @property
    def folder_name(self) -> str:
        """Return the folder name under `specs/`, e.g. ``001-source-contracts``."""
        return f"{self.id}-{self.slug}"

    @property
    def branch_name(self) -> str:
        """Return the git branch the work happens on, e.g. ``spec/001-source-contracts``."""
        return f"spec/{self.folder_name}"

    @property
    def outside_catalogue(self) -> bool:
        """Return whether this is a feature that serves no RT of the catalogue (ADR-0014)."""
        return self.kind is DossierKind.FEATURE and not self.requirements

    @property
    def needs_rationale(self) -> bool:
        """Return whether `rationale` is mandatory: for enablers and work outside the catalogue."""
        return self.kind is DossierKind.ENABLER or self.outside_catalogue

    def approvals_for(self, gate_id: GateId) -> tuple[Approval, ...]:
        """Return the approvals recorded for a gate (empty when none).

        Args:
            gate_id: the gate.
        """
        return tuple(self.approvals.get(gate_id, ()))

    def with_approval(self, gate_id: GateId, approval: Approval) -> Dossier:
        """Return a copy with `approval` recorded, replacing the member's earlier one.

        Args:
            gate_id: the human gate approved.
            approval: the new approval.

        Returns:
            A new dossier; `self` is unchanged.
        """
        kept = tuple(a for a in self.approvals_for(gate_id) if a.member != approval.member)
        approvals = dict(self.approvals)
        approvals[gate_id] = (*kept, approval)
        return replace(self, approvals=approvals)

    def with_verification(self, verification: Verification) -> Dossier:
        """Return a copy whose G5 evidence is `verification`.

        Args:
            verification: the result of the latest run of the quality suite.
        """
        return replace(self, verification=verification)
