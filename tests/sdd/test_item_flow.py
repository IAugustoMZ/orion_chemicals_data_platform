"""Unit tests of `item next` and `item merged`, with an in-memory git."""

from __future__ import annotations

import pytest

from sdd.application.use_cases.item_flow import MarkItemMerged, NextItem
from sdd.domain.errors import GateOrderError, ItemRefusedError
from sdd.domain.item_progress import ItemState
from tests.sdd.fake_git import FakeGit
from tests.sdd.fakes import NOW, FixedClock
from tests.sdd.test_item_use_cases import Items

MERGED_PATH = (ItemState.VERIFIED, ItemState.PR_OPEN, ItemState.MERGED)


class Flow:
    """Dossier 001 through G4, card 01 approved, with the flow use cases on a fake git."""

    def __init__(self, git: FakeGit | None = None) -> None:
        self.items = Items()
        self.items.approve_both("01")
        self.git = git or FakeGit()
        self.next = NextItem(self.items.cards, self.items.progress, self.items.evaluate, self.git)
        self.merged = MarkItemMerged(self.items.cards, self.items.progress, self.git, FixedClock())

    def move(self, number: str, *states: ItemState) -> None:
        stored = self.items.cards.progress("001")
        for state in states:
            stored = stored.move(number, state)
        self.items.progress.save("001", stored)

    def branch_of(self, number: str, branch: str) -> None:
        stored = self.items.cards.progress("001")
        self.items.progress.save("001", stored.with_branch(number, branch))

    def state(self, number: str) -> ItemState:
        return self.items.progress.load("001").record(number).state


class TestNextItem:
    @pytest.mark.ac("PBI-002-03:AC1")
    def test_syncs_main_tidies_merged_branches_and_creates_the_next_branch(self):
        flow = Flow()
        flow.move("01", *MERGED_PATH)
        result = flow.next.execute("001")
        assert (result.number, result.branch) == ("02", "feat/001-02-second")
        assert result.deleted == ("feat/001-01-first",)
        assert flow.git.calls == [
            "switch main",
            "ff main",
            "delete feat/001-01-first",
            "create feat/001-02-second",
        ]
        assert flow.items.progress.load("001").record("02").branch == "feat/001-02-second"

    @pytest.mark.ac("PBI-002-03:AC1")
    def test_an_approved_card_starts_building_and_progress_changes_are_not_dirt(self):
        flow = Flow(FakeGit(dirty=("specs/001-demo/progress.yaml",)))
        flow.items.approve_both("02")
        flow.move("01", *MERGED_PATH)
        flow.next.execute("001")
        assert flow.state("02") is ItemState.BUILDING

    @pytest.mark.ac("PBI-002-03:AC2")
    def test_a_card_that_is_not_merged_stops_the_flow_and_changes_nothing(self):
        flow = Flow()
        flow.move("01", ItemState.BUILDING)
        flow.branch_of("01", "feat/001-01-first")
        with pytest.raises(ItemRefusedError) as error:
            flow.next.execute("001")
        assert "card 01 is not merged" in error.value.problems[0]
        assert flow.git.calls == []

    @pytest.mark.ac("PBI-002-03:AC2")
    def test_dirty_tree_unmerged_branch_and_unreachable_remote_are_all_named(self):
        git = FakeGit(dirty=("tools/x.py",))
        git.branches.add("feat/001-09-wip")
        flow = Flow(git)
        flow.move("01", *MERGED_PATH)
        with pytest.raises(ItemRefusedError) as error:
            flow.next.execute("001")
        text = " | ".join(error.value.problems)
        assert "tools/x.py" in text and "feat/001-09-wip" in text
        git.reachable = False
        with pytest.raises(ItemRefusedError, match="remote"):
            flow.next.execute("001")
        assert git.calls == []

    @pytest.mark.ac("PBI-002-03:AC2")
    def test_a_failed_fast_forward_stops_before_any_deletion(self):
        flow = Flow(FakeGit(can_fast_forward=False))
        flow.move("01", *MERGED_PATH)
        with pytest.raises(ItemRefusedError):
            flow.next.execute("001")
        assert not any(c.startswith(("delete", "create")) for c in flow.git.calls)

    def test_nothing_is_left_when_every_card_is_merged(self):
        flow = Flow()
        flow.items.approve_both("02")
        flow.move("01", *MERGED_PATH)
        flow.move("02", *MERGED_PATH)
        with pytest.raises(ItemRefusedError, match="every card"):
            flow.next.execute("001")

    def test_cards_start_only_after_g4(self):
        flow = Flow()
        dossier = flow.items.dossiers.load("001")
        flow.items.dossiers.save(dossier.__class__(**{**dossier.__dict__, "approvals": {}}))
        with pytest.raises(GateOrderError):
            flow.next.execute("001")


class TestMarkItemMerged:
    def _verified(self, flow: Flow) -> None:
        flow.move("01", ItemState.VERIFIED)
        flow.branch_of("01", "feat/001-01-first")
        flow.git.tips["feat/001-01-first"] = "c0ffee"

    @pytest.mark.ac("PBI-002-03:AC3")
    def test_a_commit_not_in_origin_main_is_refused_and_the_card_stays_pr_open(self):
        flow = Flow()
        self._verified(flow)
        with pytest.raises(ItemRefusedError, match="not in origin/main"):
            flow.merged.execute("001", "01")
        record = flow.items.progress.load("001").record("01")
        assert (record.state, record.commit) == (ItemState.PR_OPEN, "c0ffee")

    @pytest.mark.ac("PBI-002-03:AC3")
    def test_a_commit_in_origin_main_records_the_merge(self):
        flow = Flow()
        self._verified(flow)
        flow.git.in_main.add("c0ffee")
        record = flow.merged.execute("001", "01")
        assert (record.state, record.merged_at) == (ItemState.MERGED, NOW)

    def test_an_unverified_card_an_unreachable_remote_and_no_commit_are_refused(self):
        flow = Flow()
        with pytest.raises(ItemRefusedError, match="verified"):
            flow.merged.execute("001", "01")
        self._verified(flow)
        flow.git.reachable = False
        with pytest.raises(ItemRefusedError, match="remote"):
            flow.merged.execute("001", "01")
        flow.git.reachable = True
        flow.git.tips.clear()
        with pytest.raises(ItemRefusedError, match="no commit"):
            flow.merged.execute("001", "01")
