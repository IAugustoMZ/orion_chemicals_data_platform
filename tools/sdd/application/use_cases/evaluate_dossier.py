"""Use case: evaluate the gates of one dossier, or of all of them.

Application layer. This is the read model of the harness: `sdd status`, `sdd check`, the
generators of the README and of the traceability matrix, and the approval and verification use
cases all start from a `DossierReport`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sdd.application.evidence import collect_evidence
from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import Workspace
from sdd.application.ports.reference_data import RequirementCatalog, TeamDirectory
from sdd.domain.dossier import Dossier
from sdd.domain.gate_status import (
    GateEvidence,
    GateStatus,
    current_gate,
    evaluate_gates,
)
from sdd.domain.gates import GateId
from sdd.domain.requirement import Requirement
from sdd.domain.team import Team


@dataclass(frozen=True)
class DossierReport:
    """A dossier together with the evaluated state of its eight gates.

    Attributes:
        dossier: the dossier as stored.
        statuses: one status per gate, G0 first.
        evidence: the digests and G0 problems the statuses were computed from.
    """

    dossier: Dossier
    statuses: tuple[GateStatus, ...]
    evidence: GateEvidence

    def status(self, gate_id: GateId) -> GateStatus:
        """Return the status of one gate.

        Args:
            gate_id: the gate.
        """
        return next(s for s in self.statuses if s.gate.id is gate_id)

    @property
    def current(self) -> GateStatus | None:
        """Return the first gate that has not passed, or None when the dossier is complete."""
        return current_gate(self.statuses)


class EvaluateDossier:
    """Compute `DossierReport` values from the stored dossiers and the files as they are now."""

    def __init__(
        self,
        dossiers: DossierRepository,
        requirements: RequirementCatalog,
        team: TeamDirectory,
        workspace: Workspace,
    ) -> None:
        """Receive the ports the evaluation reads from.

        Args:
            dossiers: the dossier store.
            requirements: the RT catalogue (for gate G0).
            team: the approvers and policy (for the human gates).
            workspace: git facts, here the governed digest (for gate G5).
        """
        self._dossiers = dossiers
        self._requirements = requirements
        self._team = team
        self._workspace = workspace

    def one(self, dossier_id: str) -> DossierReport:
        """Evaluate one dossier.

        Args:
            dossier_id: three-digit id.

        Raises:
            DossierNotFoundError: when it does not exist.
        """
        dossier = self._dossiers.load(dossier_id)
        catalog, team = self._requirements.all(), self._team.load()
        return self._report(dossier, catalog, team, self._workspace.governed_digest())

    def all(self) -> tuple[DossierReport, ...]:
        """Evaluate every dossier, computing the expensive governed digest only once."""
        catalog, team = self._requirements.all(), self._team.load()
        governed = self._workspace.governed_digest()
        return tuple(
            self._report(self._dossiers.load(dossier_id), catalog, team, governed)
            for dossier_id in self._dossiers.ids()
        )

    def _report(
        self, dossier: Dossier, catalog: Mapping[str, Requirement], team: Team, governed: str
    ) -> DossierReport:
        """Build the report of one loaded dossier.

        Args:
            dossier: the dossier.
            catalog: the RT catalogue by id.
            team: the approvers and policy.
            governed: the current governed digest.
        """
        evidence = collect_evidence(dossier, self._dossiers, catalog, governed)
        return DossierReport(dossier, evaluate_gates(dossier, team, evidence), evidence)
