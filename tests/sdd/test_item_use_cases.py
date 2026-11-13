"""Unit tests of the per-card use cases with in-memory fakes."""

from __future__ import annotations

import pytest

from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.application.use_cases.items import ApproveItem, ItemCards, VerifyItem
from sdd.domain.errors import (
    ApprovalDeclinedError,
    GateOrderError,
    ItemRefusedError,
    UnknownItemError,
)
from sdd.domain.gates import GateId
from sdd.domain.item_progress import ItemState
from tests.sdd.fakes import (
    FakeAcReader,
    FakeCatalog,
    FakeChecks,
    FakeConfirmation,
    FakeProgress,
    FakeRunner,
    FakeTeam,
    FakeWorkspace,
    FixedClock,
)
from tests.sdd.test_item_progress import BACKLOG
from tests.sdd.test_use_cases import World


class Items:
    """A dossier through G4 with a two-card backlog, and the per-card use cases."""

    def __init__(self, verdict: dict[str, bool] | None = None, approves: bool = True) -> None:
        self.world = World()
        self.world.ready_dossier()
        self.world.dossiers.write("001", "backlog.md", BACKLOG)
        self.world.approve_through(GateId.G4)
        self.dossiers = self.world.dossiers
        self.progress = FakeProgress()
        self.evaluate = EvaluateDossier(
            self.dossiers, FakeCatalog(), FakeTeam(), FakeWorkspace(), self.progress
        )
        self.cards = ItemCards(self.dossiers, self.progress, FakeTeam())
        self.runner = FakeRunner()
        self.confirmation = FakeConfirmation(approves)
        self.approve = ApproveItem(
            self.cards,
            self.progress,
            self.evaluate,
            FakeTeam(),
            FakeWorkspace(),
            self.confirmation,
            FixedClock(),
        )
        self.verify = VerifyItem(
            self.cards,
            self.progress,
            self.evaluate,
            FakeAcReader(verdict or {}),
            FakeChecks(),
            self.runner,
        )

    def approve_both(self, number: str = "01") -> None:
        for member in ("mentor", "mentee"):
            self.approve.execute("001", number, member, "")


PASSING = {"PBI-001-01:AC1": True, "PBI-001-01:AC2": True}


class TestApproveItem:
    def test_one_approval_refines_two_approve(self):
        items = Items()
        view = items.approve.execute("001", "01", "mentor", "")
        assert (view.state, view.missing) == (ItemState.REFINED, ("mentee",))
        view = items.approve.execute("001", "01", "mentee", "")
        assert (view.state, view.approved) == (ItemState.APPROVED, True)
        assert "Card" in items.confirmation.shown[0]

    def test_declined_confirmation_saves_nothing(self):
        items = Items(approves=False)
        with pytest.raises(ApprovalDeclinedError):
            items.approve.execute("001", "01", "mentor", "")
        assert items.progress.load("001") is None

    def test_unknown_card_is_refused(self):
        with pytest.raises(UnknownItemError):
            Items().approve.execute("001", "09", "mentor", "")

    def test_cards_are_not_approved_before_g4(self):
        items = Items()
        items.dossiers.save(
            items.dossiers.load("001").__class__(
                **{**items.dossiers.load("001").__dict__, "approvals": {}}
            )
        )
        with pytest.raises(GateOrderError):
            items.approve.execute("001", "01", "mentor", "")

    @pytest.mark.ac("PBI-002-02:AC2")
    def test_changing_a_card_stales_its_approvals_only(self):
        items = Items()
        items.approve_both("01")
        items.approve_both("02")
        items.dossiers.write("001", "backlog.md", BACKLOG.replace("- AC1: c", "- AC1: new"))
        first, second = items.cards.one("001", "01"), items.cards.one("001", "02")
        assert first.approved and not second.approved
        assert second.stale == ("mentor", "mentee")


class TestVerifyItem:
    @pytest.mark.ac("PBI-002-02:AC1")
    def test_an_unapproved_card_is_refused_before_any_check(self):
        items = Items(PASSING)
        items.approve.execute("001", "01", "mentor", "")
        with pytest.raises(ItemRefusedError) as error:
            items.verify.execute("001", "01")
        assert "missing: mentee" in error.value.problems[0]
        assert items.progress.load("001").record("01").state is ItemState.REFINED

    @pytest.mark.ac("PBI-002-02:AC3")
    def test_an_ac_without_a_passing_marked_test_fails_and_is_listed(self):
        items = Items({"PBI-001-01:AC1": False})
        items.approve_both()
        with pytest.raises(ItemRefusedError) as error:
            items.verify.execute("001", "01")
        assert error.value.problems == (
            "PBI-001-01:AC1 has a marked test that fails",
            'PBI-001-01:AC2 has no test marked with @pytest.mark.ac("PBI-001-01:AC2")',
        )

    @pytest.mark.ac("PBI-002-02:AC3")
    def test_a_covered_card_runs_the_suite_and_becomes_verified(self):
        items = Items(PASSING)
        items.approve_both()
        seen = []
        outcomes = items.verify.execute("001", "01", lambda c, o: seen.append(o is None))
        assert all(o.passed for o in outcomes) and seen == [True, False, True, False]
        assert items.progress.load("001").record("01").state is ItemState.VERIFIED

    def test_a_failing_check_keeps_the_card_approved(self):
        items = Items(PASSING)
        items.runner.failing = {"tests"}
        items.approve_both()
        outcomes = items.verify.execute("001", "01")
        assert [o.passed for o in outcomes] == [True, False]
        assert items.progress.load("001").record("01").state is ItemState.APPROVED

    @pytest.mark.ac("PBI-002-02:AC4")
    def test_view_of_every_card_and_g5_waits_for_the_merges(self):
        items = Items()
        assert [v.number for v in items.cards.all("001")] == ["01", "02"]
        assert items.cards.progress("001").items == {}
        assert items.evaluate.one("001").evidence.unmerged_cards is None
        items.approve_both()
        assert items.evaluate.one("001").evidence.unmerged_cards == ("01", "02")
