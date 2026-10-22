"""Gate evaluation: turn a dossier and the current state of the files into gate states.

Domain layer, pure function. Nothing is stored about whether a gate "is passed": it is computed
every time from the evidence (approvals, verification) and the *current* digests. That is what
makes a stale approval visible the moment an approved artifact is edited.

States (see the state machine in `harness/how-it-works.md`):

* ``passed``   the gate's condition holds for the current content.
* ``pending``  nothing recorded yet.
* ``partial``  some of us approved the current content, others still have to.
* ``stale``    there were approvals or a verification, but the content changed since.
* ``failed``   an automated gate ran and said no.
* ``blocked``  an earlier gate has not passed, so this one cannot be judged yet.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from sdd.domain.digest import short
from sdd.domain.dossier import Dossier
from sdd.domain.gates import GATES, GateDefinition, GateId, GateKind
from sdd.domain.team import Team


class GateState(StrEnum):
    """Evaluated state of a gate (see the module docstring)."""

    PASSED = "passed"
    PENDING = "pending"
    PARTIAL = "partial"
    STALE = "stale"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class GateEvidence:
    """What the evaluation needs to know about the files right now.

    Attributes:
        artifact_digests: current digest of each human gate's artifacts.
        governed_digest: current digest of the governed code (compared with G5's verification).
        context_problems: problems with the requirement citations (G0); empty means G0 passes.
    """

    artifact_digests: Mapping[GateId, str]
    governed_digest: str
    context_problems: tuple[str, ...]


@dataclass(frozen=True)
class GateStatus:
    """The evaluated state of one gate of one dossier.

    Attributes:
        gate: the gate definition.
        state: the evaluated state.
        detail: one sentence explaining the state (what is missing, who must approve).
        approved_by: members whose approval matches the current content.
    """

    gate: GateDefinition
    state: GateState
    detail: str
    approved_by: tuple[str, ...] = ()


def evaluate_gates(dossier: Dossier, team: Team, evidence: GateEvidence) -> tuple[GateStatus, ...]:
    """Evaluate every gate of a dossier in lifecycle order.

    Args:
        dossier: the dossier and its recorded approvals/verification.
        team: who must approve human gates, and the policy.
        evidence: current digests and G0 problems.

    Returns:
        One status per gate, G0 first. A gate after a non-passed gate is ``blocked``.
    """
    statuses: list[GateStatus] = []
    waiting_for: GateId | None = None
    for gate in GATES:
        own = _own_status(gate, dossier, team, evidence)
        if waiting_for is not None:
            own = GateStatus(gate, GateState.BLOCKED, f"waits for {waiting_for}", own.approved_by)
        elif own.state is not GateState.PASSED:
            waiting_for = gate.id
        statuses.append(own)
    return tuple(statuses)


def current_gate(statuses: tuple[GateStatus, ...]) -> GateStatus | None:
    """Return the first gate that has not passed (where the work is), or None when all passed.

    Args:
        statuses: the result of `evaluate_gates`.
    """
    return next((s for s in statuses if s.state is not GateState.PASSED), None)


def _own_status(
    gate: GateDefinition, dossier: Dossier, team: Team, evidence: GateEvidence
) -> GateStatus:
    """Evaluate one gate on its own evidence, ignoring the gates before it.

    Args:
        gate: the gate to evaluate.
        dossier: the dossier.
        team: approvers and policy.
        evidence: current digests and G0 problems.
    """
    if gate.id is GateId.G0:
        return _context_status(gate, evidence)
    if gate.kind is GateKind.AUTOMATED:
        return _verification_status(gate, dossier, evidence)
    return _approval_status(gate, dossier, team, evidence.artifact_digests[gate.id])


def _context_status(gate: GateDefinition, evidence: GateEvidence) -> GateStatus:
    """G0 passes when the dossier's requirement citations are valid.

    Args:
        gate: the G0 definition.
        evidence: holds the citation problems found by the application layer.
    """
    if evidence.context_problems:
        return GateStatus(gate, GateState.FAILED, "; ".join(evidence.context_problems))
    return GateStatus(gate, GateState.PASSED, "requirements cited and known")


def _verification_status(
    gate: GateDefinition, dossier: Dossier, evidence: GateEvidence
) -> GateStatus:
    """G5 passes when the latest verification passed on the current governed code.

    Args:
        gate: the G5 definition.
        dossier: holds the latest verification.
        evidence: holds the current governed digest.
    """
    verification = dossier.verification
    if verification is None:
        return GateStatus(gate, GateState.PENDING, "run `sdd verify`")
    if verification.digest != evidence.governed_digest:
        return GateStatus(gate, GateState.STALE, "code changed since the last `sdd verify`")
    if not verification.passed:
        failing = ", ".join(verification.failed_checks) or "no check ran"
        return GateStatus(gate, GateState.FAILED, f"failing: {failing}")
    return GateStatus(gate, GateState.PASSED, f"verified at {short(verification.digest)}")


def _approval_status(
    gate: GateDefinition, dossier: Dossier, team: Team, current_digest: str
) -> GateStatus:
    """A human gate passes when the team policy is satisfied by approvals of current content.

    Args:
        gate: the human gate.
        dossier: holds the approvals.
        team: approvers and policy.
        current_digest: digest of the gate's artifacts as they are now.
    """
    approvals = dossier.approvals_for(gate.id)
    fresh = tuple(a.member for a in approvals if a.digest == current_digest)
    outdated = tuple(a.member for a in approvals if a.digest != current_digest)
    missing = team.missing_approvers(fresh)
    if not missing:
        return GateStatus(gate, GateState.PASSED, f"approved by {', '.join(fresh)}", fresh)
    if outdated and not fresh:
        detail = f"artifacts changed after approval by {', '.join(outdated)}; re-approve"
        return GateStatus(gate, GateState.STALE, detail)
    if fresh:
        return GateStatus(gate, GateState.PARTIAL, f"waiting for {', '.join(missing)}", fresh)
    return GateStatus(gate, GateState.PENDING, f"needs approval by {', '.join(missing)}")
