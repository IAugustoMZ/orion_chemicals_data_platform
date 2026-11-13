"""Unit tests of the per-card domain: sections, digests, state machine, gate rules."""

from __future__ import annotations

import pytest

from sdd.domain.approval import Approval, CheckOutcome, Verification
from sdd.domain.card_digest import (
    acceptance_criteria,
    backlog_without_card_bodies,
    card_digest,
    card_sections,
)
from sdd.domain.errors import IllegalTransitionError
from sdd.domain.gate_status import GateEvidence, GateState, evaluate_gates
from sdd.domain.gates import GateId
from sdd.domain.governance import item_branch_name, item_from_branch
from sdd.domain.item_progress import ItemProgress, ItemState
from tests.sdd.fakes import NOW, TEAM, dossier

BACKLOG = """# Backlog
## Work items
### PBI-001-01 · First
- AC1: a
- AC2: b
### PBI-001-02 · Second
- AC1: c
## Section
Done and reviewed.
## Order
text
"""


def approval(member: str, digest: str) -> Approval:
    return Approval(member, NOW, digest, "Ana")


class TestCards:
    def test_sections_are_split_by_card(self):
        sections = card_sections(BACKLOG)
        assert list(sections) == ["01", "02"]
        assert "Second" in sections["02"] and "Order" not in sections["02"]

    @pytest.mark.ac("PBI-002-02:AC2")
    def test_editing_one_card_changes_only_its_digest(self):
        before = {n: card_digest(s) for n, s in card_sections(BACKLOG).items()}
        edited = BACKLOG.replace("- AC1: c", "- AC1: changed")
        after = {n: card_digest(s) for n, s in card_sections(edited).items()}
        assert before["01"] == after["01"]
        assert before["02"] != after["02"]

    def test_acceptance_criteria_in_order(self):
        assert acceptance_criteria(card_sections(BACKLOG)["01"]) == ("AC1", "AC2")

    def test_g2_text_keeps_the_first_card_only(self):
        text = backlog_without_card_bodies(BACKLOG)
        assert "- AC2: b" in text and "- AC1: c" not in text
        assert "### PBI-001-02 · Second" in text and "## Order" in text


class TestStateMachine:
    def test_approvals_walk_outline_refined_approved(self):
        progress = ItemProgress().with_approval("01", approval("mentor", "d"), complete=False)
        assert progress.record("01").state is ItemState.REFINED
        progress = progress.with_approval("01", approval("mentee", "d"), complete=True)
        assert progress.record("01").state is ItemState.APPROVED
        assert progress.record("01").fresh_approvers("d") == ("mentor", "mentee")
        assert progress.record("01").fresh_approvers("other") == ()

    def test_a_member_approval_is_replaced_not_duplicated(self):
        progress = ItemProgress().with_approval("01", approval("mentor", "d1"), complete=False)
        progress = progress.with_approval("01", approval("mentor", "d2"), complete=False)
        assert len(progress.record("01").approvals) == 1

    def test_illegal_step_is_refused_and_same_state_is_a_no_op(self):
        progress = ItemProgress()
        with pytest.raises(IllegalTransitionError):
            progress.move("01", ItemState.MERGED)
        assert progress.move("01", ItemState.OUTLINE) is progress

    def test_unmerged_lists_the_cards_still_open(self):
        assert ItemProgress().unmerged(("01", "02")) == ("01", "02")


class TestGateRules:
    def _g5(self, unmerged: tuple[str, ...] | None) -> GateState:
        verified = dossier().with_verification(
            Verification(NOW, "sha256:c", "abc", (CheckOutcome("lint", True, "ok"),))
        )
        for gate in (GateId.G1, GateId.G2, GateId.G3, GateId.G4):
            for member in ("mentor", "mentee"):
                verified = verified.with_approval(gate, approval(member, "d"))
        evidence = GateEvidence({g: "d" for g in GateId}, "sha256:c", (), unmerged)
        return evaluate_gates(verified, TEAM, evidence)[5].state

    @pytest.mark.ac("PBI-002-02:AC4")
    def test_g5_waits_for_every_card_to_be_merged(self):
        assert self._g5(("02",)) is GateState.PENDING

    @pytest.mark.ac("PBI-002-02:AC4")
    def test_g5_passes_when_all_merged_or_without_progress_file(self):
        assert self._g5(()) is GateState.PASSED
        assert self._g5(None) is GateState.PASSED


class TestRecordedFacts:
    def test_branch_commit_and_merge_are_recorded_in_order(self):
        progress = ItemProgress().with_approval("01", approval("mentor", "d"), complete=True)
        progress = progress.with_branch("01", "feat/001-01-first").move("01", ItemState.VERIFIED)
        progress = progress.opened("01", "c0ffee")
        assert progress.record("01").state is ItemState.PR_OPEN
        record = progress.merged("01", NOW).record("01")
        assert (record.branch, record.commit, record.merged_at) == (
            "feat/001-01-first",
            "c0ffee",
            NOW,
        )
        assert record.state is ItemState.MERGED


class TestBranches:
    def test_card_branch_names_round_trip(self):
        name = item_branch_name("002", "03", "PBI-002-03 · Item flow: branch, merge and guard!")
        assert name == "feat/002-03-item-flow-branch-merge-and-guard"
        assert item_from_branch(name) == ("002", "03")
        assert item_from_branch("spec/002-harness") is None

    def test_long_titles_are_cut_at_a_word(self):
        name = item_branch_name("002", "03", "PBI-002-03 · " + "word " * 20)
        assert len(name) <= len("feat/002-03-") + 40 and not name.endswith("-")
        assert item_branch_name("002", "03", "PBI-002-03 · ??") == "feat/002-03-card"
