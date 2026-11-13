"""Use cases of the per-card flow: view, approve and verify one backlog card (ADR-0023).

Application layer. A card's approval is bound to the digest of its own section of `backlog.md`;
verification refuses a card that is not approved for its current text, or whose acceptance
criteria lack a passing marked test, and only then runs the quality suite.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import CheckRunner, Clock, HumanConfirmation, Workspace
from sdd.application.ports.progress import AcStatusReader, ProgressRepository
from sdd.application.ports.reference_data import QualityCheckCatalog, TeamDirectory
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.domain.approval import Approval, CheckOutcome
from sdd.domain.card_digest import acceptance_criteria, card_digest, card_sections
from sdd.domain.digest import short
from sdd.domain.errors import (
    ApprovalDeclinedError,
    GateOrderError,
    ItemRefusedError,
    UnknownItemError,
)
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId
from sdd.domain.item_progress import ItemProgress, ItemRecord, ItemState
from sdd.domain.quality import QualityCheck


@dataclass(frozen=True)
class ItemView:
    """One card as people see it.

    Attributes:
        number: the card number.
        title: the heading text of the card.
        state: the stored state.
        approved_by: members whose approval matches the card as it is now.
        missing: members who still have to approve the current text.
        stale: members whose approval is for an older text.
    """

    number: str
    title: str
    state: ItemState
    approved_by: tuple[str, ...]
    missing: tuple[str, ...]
    stale: tuple[str, ...]

    @property
    def approved(self) -> bool:
        """Return whether the team policy holds for the card's current text."""
        return not self.missing


class ItemCards:
    """Read the cards of a dossier together with their recorded progress."""

    def __init__(
        self,
        dossiers: DossierRepository,
        progress: ProgressRepository,
        team: TeamDirectory,
    ) -> None:
        """Receive the ports the view reads from.

        Args:
            dossiers: where `backlog.md` is read.
            progress: where `progress.yaml` is read.
            team: the approvers and policy.
        """
        self._dossiers = dossiers
        self._progress = progress
        self._team = team

    def sections(self, dossier_id: str) -> dict[str, str]:
        """Return the backlog cards of the dossier by number.

        Args:
            dossier_id: three-digit dossier id.
        """
        dossier = self._dossiers.load(dossier_id)
        return card_sections(self._dossiers.read_artifact(dossier, "backlog.md") or "")

    def progress(self, dossier_id: str) -> ItemProgress:
        """Return the stored progress, or an empty one when the file does not exist.

        Args:
            dossier_id: three-digit dossier id.
        """
        return self._progress.load(dossier_id) or ItemProgress()

    def all(self, dossier_id: str) -> tuple[ItemView, ...]:
        """Return a view of every card, in backlog order.

        Args:
            dossier_id: three-digit dossier id.
        """
        stored = self.progress(dossier_id)
        views = []
        for number, section in self.sections(dossier_id).items():
            views.append(self._view(number, section, stored.record(number)))
        return tuple(views)

    def one(self, dossier_id: str, number: str) -> ItemView:
        """Return the view of one card.

        Args:
            dossier_id: three-digit dossier id.
            number: the card number, ``"02"``.

        Raises:
            UnknownItemError: when the backlog has no such card.
        """
        sections = self.sections(dossier_id)
        if number not in sections:
            raise UnknownItemError(f"dossier {dossier_id} has no card {number}")
        return self._view(number, sections[number], self.progress(dossier_id).record(number))

    def _view(self, number: str, section: str, record: ItemRecord) -> ItemView:
        """Build the view of one card against its current digest.

        Args:
            number: the card number.
            section: the card's section text.
            record: the stored record.
        """
        digest = card_digest(section)
        fresh = record.fresh_approvers(digest)
        stale = tuple(a.member for a in record.approvals if a.digest != digest)
        title = section.splitlines()[0].removeprefix("### ").strip()
        missing = self._team.load().missing_approvers(fresh)
        return ItemView(number, title, record.state, fresh, missing, stale)


class ApproveItem:
    """Record one member's approval of one card, for the card's current text."""

    def __init__(
        self,
        cards: ItemCards,
        progress: ProgressRepository,
        evaluator: EvaluateDossier,
        team: TeamDirectory,
        workspace: Workspace,
        confirmation: HumanConfirmation,
        clock: Clock,
    ) -> None:
        """Receive the ports an approval needs.

        Args:
            cards: reads the cards and their progress.
            progress: where the approval is saved.
            evaluator: to require that G4 passed.
            team: the approvers.
            workspace: git identity for the audit trail.
            confirmation: the human-at-the-terminal check.
            clock: the approval time.
        """
        self._cards = cards
        self._progress = progress
        self._evaluator = evaluator
        self._team = team
        self._workspace = workspace
        self._confirmation = confirmation
        self._clock = clock

    def execute(self, dossier_id: str, number: str, member_id: str, note: str) -> ItemView:
        """Approve card `number` of dossier `dossier_id` as `member_id`.

        Args:
            dossier_id: three-digit dossier id.
            number: the card number.
            member_id: the approver's id in `harness/team.yaml`.
            note: optional remark kept with the approval.

        Returns:
            The card as it is after the approval.

        Raises:
            UnknownItemError, UnknownMemberError, GateOrderError, HumanConfirmationRequiredError,
            ApprovalDeclinedError: when the approval cannot be recorded.
        """
        team = self._team.load()
        member = team.member(member_id)
        report = self._evaluator.one(dossier_id)
        status = report.status(GateId.G4)
        if status.state is not GateState.PASSED:
            raise GateOrderError(f"cards are approved after G4 passes; it is {status.state}")
        view = self._cards.one(dossier_id, number)
        digest = card_digest(self._cards.sections(dossier_id)[number])
        summary = "\n".join(
            (
                f"Dossier   {dossier_id}  {report.dossier.title}",
                f"Card      {view.title}",
                f"Digest    {short(digest)}",
                f"Approver  {member.id} ({member.name}, {member.role})",
            )
        )
        if not self._confirmation.confirm(summary):
            raise ApprovalDeclinedError("approval cancelled; nothing saved")
        approval = Approval(
            member.id, self._clock.now(), digest, self._workspace.git_identity(), note.strip()
        )
        stored = self._cards.progress(dossier_id)
        fresh = {*stored.record(number).fresh_approvers(digest), member.id}
        complete = not team.missing_approvers(fresh)
        self._progress.save(dossier_id, stored.with_approval(number, approval, complete))
        return self._cards.one(dossier_id, number)


ItemProgressCallback = Callable[[QualityCheck, CheckOutcome | None], None]
"""Called before (outcome None) and after each check of the suite."""


class VerifyItem:
    """Prove one card: approved text, a passing test per criterion, then the quality suite."""

    def __init__(
        self,
        cards: ItemCards,
        progress: ProgressRepository,
        evaluator: EvaluateDossier,
        reader: AcStatusReader,
        checks: QualityCheckCatalog,
        runner: CheckRunner,
    ) -> None:
        """Receive the ports a verification needs.

        Args:
            cards: reads the cards and their progress.
            progress: where the new state is saved.
            evaluator: to require that G4 passed.
            reader: tells which criteria have a passing marked test.
            checks: the quality suite.
            runner: runs one check.
        """
        self._cards = cards
        self._progress = progress
        self._evaluator = evaluator
        self._reader = reader
        self._checks = checks
        self._runner = runner

    def execute(
        self, dossier_id: str, number: str, on_check: ItemProgressCallback | None = None
    ) -> tuple[CheckOutcome, ...]:
        """Verify card `number`, refusing before any check runs when it is not ready.

        Args:
            dossier_id: three-digit dossier id.
            number: the card number.
            on_check: optional observer of each check (before and after it runs).

        Returns:
            The outcome of each check; the card becomes ``verified`` only if all passed.

        Raises:
            UnknownItemError, GateOrderError: when the card or the specification is not ready.
            ItemRefusedError: when the card is not approved or a criterion is not covered.
        """
        g4 = self._evaluator.one(dossier_id).status(GateId.G4)
        if g4.state is not GateState.PASSED:
            raise GateOrderError(f"cards are built after G4 passes; it is {g4.state}")
        view = self._cards.one(dossier_id, number)
        problems = _approval_problems(dossier_id, view)
        section = self._cards.sections(dossier_id)[number]
        evidence = self._reader.read()
        problems += _criteria_problems(section, evidence)
        if problems:
            raise ItemRefusedError(problems)
        outcomes = []
        for check in self._checks.all():
            if on_check:
                on_check(check, None)
            outcome = self._runner.run(check)
            outcomes.append(outcome)
            if on_check:
                on_check(check, outcome)
        if all(o.passed for o in outcomes):
            stored = self._cards.progress(dossier_id)
            self._progress.save(dossier_id, stored.move(number, ItemState.VERIFIED))
        return tuple(outcomes)


def _approval_problems(dossier_id: str, view: ItemView) -> tuple[str, ...]:
    """Return why a card is not approved for its current text.

    Args:
        dossier_id: three-digit dossier id, for the suggested command.
        view: the card.
    """
    if view.approved:
        return ()
    who = ", ".join(view.missing)
    return (
        f"card {view.number} is not approved for its current text; missing: {who}. "
        f"Each one runs: sdd item approve {dossier_id} {view.number} --as <member>",
    )


def _criteria_problems(section: str, evidence: Mapping[str, bool]) -> tuple[str, ...]:
    """Return one line per acceptance criterion without a passing marked test.

    Args:
        section: the card's section text.
        evidence: marker id to passed, from the `AcStatusReader`.
    """
    heading = section.splitlines()[0].removeprefix("### ").split(" ")[0]
    problems = []
    for criterion in acceptance_criteria(section):
        key = f"{heading}:{criterion}"
        result = evidence.get(key)
        if result is None:
            problems.append(f'{key} has no test marked with @pytest.mark.ac("{key}")')
        elif not result:
            problems.append(f"{key} has a marked test that fails")
    return tuple(problems)
