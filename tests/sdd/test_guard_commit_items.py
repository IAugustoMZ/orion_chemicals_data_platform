"""The commit guard on card branches: approved card and fresh specification are required."""

from __future__ import annotations

import pytest

from sdd.application.use_cases.guard_commit import GuardCommit
from sdd.domain.approval import Approval
from sdd.domain.gates import GateId
from tests.sdd.fakes import NOW
from tests.sdd.test_item_progress import BACKLOG
from tests.sdd.test_item_use_cases import Items


class Guarded:
    """Dossier 001 through G4 with two cards, on a card branch."""

    def __init__(self, branch: str = "feat/001-01-first") -> None:
        self.items = Items()
        self.items.world.workspace.branch = branch
        self.guard = GuardCommit(self.items.world.workspace, self.items.evaluate, self.items.cards)

    def run(self, *paths: str) -> list[str]:
        return [f.message for f in self.guard.execute(paths or ("tools/x.py",))]


class TestItemBranches:
    @pytest.mark.ac("PBI-002-03:AC5")
    def test_an_unapproved_card_blocks_governed_changes(self):
        guarded = Guarded()
        (message,) = guarded.run()
        assert "card 01" in message and "not approved" in message

    @pytest.mark.ac("PBI-002-03:AC5")
    def test_an_edited_card_blocks_again_until_it_is_re_approved(self):
        guarded = Guarded()
        guarded.items.approve_both("01")
        assert guarded.run() == []
        stored = guarded.items.cards.progress("001")
        for member in ("mentor", "mentee"):
            stored = stored.with_approval("01", Approval(member, NOW, "sha256:old", "Ana"), False)
        guarded.items.progress.save("001", stored)
        assert "not approved" in guarded.run()[0]
        guarded.items.dossiers.write("001", "backlog.md", BACKLOG.replace("- AC1: a", "- AC1: z"))
        assert guarded.run()

    @pytest.mark.ac("PBI-002-03:AC5")
    def test_another_cards_approval_does_not_open_this_branch(self):
        guarded = Guarded("feat/001-02-second")
        guarded.items.approve_both("01")
        assert "card 02" in guarded.run()[0]

    @pytest.mark.ac("PBI-002-03:AC6")
    def test_a_stale_specification_blocks_even_an_approved_card(self):
        guarded = Guarded()
        guarded.items.approve_both("01")
        guarded.items.dossiers.write("001", "spec.md", "# changed after approval\n")
        (message,) = guarded.run()
        assert "G4 is" in message

    @pytest.mark.ac("PBI-002-03:AC6")
    def test_item_verify_also_refuses_a_stale_specification(self):
        from sdd.domain.errors import GateOrderError

        guarded = Guarded()
        guarded.items.approve_both("01")
        guarded.items.dossiers.write("001", "spec.md", "# changed after approval\n")
        with pytest.raises(GateOrderError):
            guarded.items.verify.execute("001", "01")

    def test_unknown_card_and_documents_only(self):
        guarded = Guarded("feat/001-07-ghost")
        assert "no card 07" in guarded.run()[0]
        assert guarded.run("docs/a.md") == []

    def test_spec_branches_keep_working_and_g4_is_still_needed(self):
        guarded = Guarded("spec/001-demo")
        assert guarded.run() == []
        assert guarded.items.evaluate.one("001").status(GateId.G4).state.value == "passed"
