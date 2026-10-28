"""Unit tests of gate evaluation: the state machine of harness/how-it-works.md."""

from __future__ import annotations

from sdd.domain.approval import Approval, CheckOutcome, Verification
from sdd.domain.gate_status import GateEvidence, GateState, current_gate, evaluate_gates
from sdd.domain.gates import GATES, GateId, GateKind
from tests.sdd.fakes import NOW, SOLO_TEAM, TEAM, dossier

DIGESTS = {g.id: f"sha256:{g.id}" for g in GATES if g.kind is GateKind.HUMAN}


def evidence(problems: tuple[str, ...] = (), governed: str = "sha256:code") -> GateEvidence:
    return GateEvidence(DIGESTS, governed, problems)


def approve_all(value, until: GateId):
    for gate in GATES:
        if gate.id is until:
            break
        if gate.kind is GateKind.HUMAN:
            for member in ("mentor", "mentee"):
                value = value.with_approval(
                    gate.id, Approval(member, NOW, DIGESTS[gate.id], "git")
                )
    return value


def states(value, ev=None, team=TEAM):
    return {s.gate.id: s.state for s in evaluate_gates(value, team, ev or evidence())}


def test_new_dossier_waits_for_g1_and_blocks_the_rest():
    result = states(dossier())
    assert result[GateId.G0] is GateState.PASSED
    assert result[GateId.G1] is GateState.PENDING
    assert {result[g] for g in list(GateId)[2:]} == {GateState.BLOCKED}


def test_g0_fails_on_context_problems():
    assert states(dossier(), evidence(("unknown RT99",)))[GateId.G0] is GateState.FAILED


def test_one_of_two_approvals_is_partial():
    value = dossier().with_approval(GateId.G1, Approval("mentor", NOW, DIGESTS[GateId.G1], "g"))
    statuses = evaluate_gates(value, TEAM, evidence())
    g1 = statuses[1]
    assert g1.state is GateState.PARTIAL
    assert g1.approved_by == ("mentor",)
    assert "mentee" in g1.detail


def test_any_policy_passes_with_one_approval():
    value = dossier().with_approval(GateId.G1, Approval("mentor", NOW, DIGESTS[GateId.G1], "g"))
    assert states(value, team=SOLO_TEAM)[GateId.G1] is GateState.PASSED


def test_edit_after_approval_is_stale():
    value = approve_all(dossier(), GateId.G2)
    changed = GateEvidence({**DIGESTS, GateId.G1: "sha256:edited"}, "sha256:code", ())
    result = states(value, changed)
    assert result[GateId.G1] is GateState.STALE
    assert result[GateId.G2] is GateState.BLOCKED


def test_g5_pending_failed_stale_and_passed():
    value = approve_all(dossier(), GateId.G5)
    assert states(value)[GateId.G5] is GateState.PENDING
    failing = Verification(NOW, "sha256:code", "c", (CheckOutcome("tests", False, ""),))
    assert states(value.with_verification(failing))[GateId.G5] is GateState.FAILED
    passing = Verification(NOW, "sha256:code", "c", (CheckOutcome("tests", True, ""),))
    assert states(value.with_verification(passing))[GateId.G5] is GateState.PASSED
    moved = evidence(governed="sha256:code-v2")
    assert states(value.with_verification(passing), moved)[GateId.G5] is GateState.STALE


def test_complete_dossier_has_no_current_gate():
    value = approve_all(dossier(), GateId.G5)
    passing = Verification(NOW, "sha256:code", "c", (CheckOutcome("tests", True, ""),))
    value = value.with_verification(passing)
    for gate in (GateId.G6, GateId.G7):
        for member in ("mentor", "mentee"):
            value = value.with_approval(gate, Approval(member, NOW, DIGESTS[gate], "g"))
    statuses = evaluate_gates(value, TEAM, evidence())
    assert current_gate(statuses) is None
