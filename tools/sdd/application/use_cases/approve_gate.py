"""Use case: record one team member's approval of a human gate (`sdd approve`).

Application layer. This is where "governed by people" becomes mechanical. An approval is
accepted only when, in this order:

1. the gate is a human gate (automated gates are closed by machines);
2. the approver is a member of `harness/team.yaml`;
3. every earlier gate has passed (no skipping phases);
4. the gate's artifacts are complete (template sections present, no ``TODO(sdd)`` left);
5. a person at an interactive terminal typed the confirmation (agents have no terminal).

The approval is then bound to the digest of the artifacts, so any later edit makes it stale.
"""

from __future__ import annotations

from sdd.application.evidence import artifact_digest
from sdd.application.ports.documents import TemplateLibrary
from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import Clock, HumanConfirmation, Workspace
from sdd.application.ports.reference_data import TeamDirectory
from sdd.application.use_cases.evaluate_dossier import DossierReport, EvaluateDossier
from sdd.domain.approval import Approval
from sdd.domain.digest import short
from sdd.domain.errors import (
    ApprovalDeclinedError,
    GateKindError,
    GateNotReadyError,
    GateOrderError,
)
from sdd.domain.gate_status import GateState, GateStatus
from sdd.domain.gates import GateDefinition, GateId, GateKind, gates_before, get_gate
from sdd.domain.readiness import readiness_problems, required_headings
from sdd.domain.team import TeamMember


class ApproveGate:
    """Validate and record an approval, then return the gate's new status."""

    def __init__(
        self,
        dossiers: DossierRepository,
        evaluator: EvaluateDossier,
        team: TeamDirectory,
        templates: TemplateLibrary,
        workspace: Workspace,
        confirmation: HumanConfirmation,
        clock: Clock,
    ) -> None:
        """Receive the ports an approval needs.

        Args:
            dossiers: where the approval is saved.
            evaluator: computes the gates' current states.
            team: the approvers.
            templates: the templates whose headings define readiness.
            workspace: git identity for the audit trail.
            confirmation: the human-at-the-terminal check.
            clock: the approval time.
        """
        self._dossiers = dossiers
        self._evaluator = evaluator
        self._team = team
        self._templates = templates
        self._workspace = workspace
        self._confirmation = confirmation
        self._clock = clock

    def execute(self, dossier_id: str, gate_id: GateId, member_id: str, note: str) -> GateStatus:
        """Approve `gate_id` of dossier `dossier_id` as `member_id`.

        Args:
            dossier_id: three-digit dossier id.
            gate_id: a human gate (G1-G4, G6, G7).
            member_id: the approver's id in `harness/team.yaml`.
            note: optional remark kept with the approval.

        Returns:
            The gate's status after the approval (``passed`` or ``partial``).

        Raises:
            GateKindError, UnknownMemberError, GateOrderError, GateNotReadyError,
            HumanConfirmationRequiredError, ApprovalDeclinedError: see the module docstring.
        """
        gate = get_gate(gate_id)
        if gate.kind is not GateKind.HUMAN:
            raise GateKindError(f"{gate.id} is automated; it is closed by `sdd verify`")
        member = self._team.load().member(member_id)
        report = self._evaluator.one(dossier_id)
        _require_earlier_gates(report, gate)
        self._require_ready(report, gate)
        digest = artifact_digest(report.dossier, gate, self._dossiers)
        self._confirm(report, gate, member, digest)
        approval = Approval(
            member.id, self._clock.now(), digest, self._workspace.git_identity(), note.strip()
        )
        self._dossiers.save(report.dossier.with_approval(gate.id, approval))
        return self._evaluator.one(dossier_id).status(gate.id)

    def _require_ready(self, report: DossierReport, gate: GateDefinition) -> None:
        """Raise when an artifact of the gate is missing, incomplete or has placeholders.

        Args:
            report: the dossier's current report.
            gate: the gate being approved.
        """
        problems: list[str] = []
        for name in gate.artifacts:
            text = self._dossiers.read_artifact(report.dossier, name)
            headings = required_headings(self._templates.text(name))
            problems.extend(readiness_problems(name, text, headings))
        if problems:
            raise GateNotReadyError(tuple(problems))

    def _confirm(
        self, report: DossierReport, gate: GateDefinition, member: TeamMember, digest: str
    ) -> None:
        """Ask the person at the terminal to type the confirmation text.

        Args:
            report: the dossier's current report.
            gate: the gate being approved.
            member: the approver.
            digest: the digest the approval will be bound to.
        """
        dossier = report.dossier
        summary = "\n".join(
            (
                f"Dossier   {dossier.id}  {dossier.title}",
                f"Gate      {gate.id}  {gate.phase_name}: {gate.title}",
                f"Artifacts {', '.join(gate.artifacts)} in {self._dossiers.location(dossier)}",
                f"Digest    {short(digest)}",
                f"Approver  {member.id} ({member.name}, {member.role})",
            )
        )
        expected = f"{dossier.id} {gate.id}"
        if not self._confirmation.confirm(summary, expected):
            raise ApprovalDeclinedError(f"confirmation did not match {expected!r}; nothing saved")


def _require_earlier_gates(report: DossierReport, gate: GateDefinition) -> None:
    """Raise when a gate before `gate` has not passed.

    Args:
        report: the dossier's current report.
        gate: the gate being approved.
    """
    for earlier in gates_before(gate.id):
        status = report.status(earlier.id)
        if status.state is not GateState.PASSED:
            raise GateOrderError(
                f"{gate.id} cannot be approved: {earlier.id} is {status.state} ({status.detail})"
            )
