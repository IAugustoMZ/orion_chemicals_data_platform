"""Use cases that move the per-card flow along: start the next card, record a merged one.

Application layer (ADR-0023). Both talk to git only through the `GitRepository` port, which can
neither force-push, hard-delete nor merge: a person merges the pull request, and the harness
records it only after git confirms that the card's commit is in ``origin/main``.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdd.application.ports.environment import Clock, Workspace
from sdd.application.ports.git import GitRepository
from sdd.application.ports.progress import ProgressRepository
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.application.use_cases.items import ItemCards
from sdd.domain.errors import GateOrderError, ItemRefusedError
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId
from sdd.domain.governance import item_branch_name, item_from_branch
from sdd.domain.item_progress import ItemRecord, ItemState

MAIN = "main"
REMOTE_MAIN = "origin/main"
_STARTED = (ItemState.BUILDING, ItemState.VERIFIED, ItemState.PR_OPEN)


@dataclass(frozen=True)
class NextItemResult:
    """What `item next` did.

    Attributes:
        number: the card whose branch was created.
        branch: the new branch, now checked out.
        deleted: the merged local branches that were removed.
    """

    number: str
    branch: str
    deleted: tuple[str, ...]


class CurrentItem:
    """Tell which card a branch builds, so CI and people need not parse branch names."""

    def __init__(self, workspace: Workspace) -> None:
        """Receive the workspace that knows the checked-out branch.

        Args:
            workspace: the working tree.
        """
        self._workspace = workspace

    def execute(self, branch: str | None = None) -> tuple[str, str]:
        """Return the dossier id and card number of a card branch.

        Args:
            branch: the branch to read; the checked-out one when omitted.

        Raises:
            ItemRefusedError: when the branch is not a ``feat/<id>-<nn>-<slug>`` card branch.
        """
        name = branch if branch is not None else self._workspace.current_branch()
        found = item_from_branch(name)
        if found is None:
            raise ItemRefusedError((f"{name or 'a detached HEAD'} is not a card branch",))
        return found


class NextItem:
    """Sync ``main``, tidy merged branches and open the branch of the next card."""

    def __init__(
        self,
        cards: ItemCards,
        progress: ProgressRepository,
        evaluator: EvaluateDossier,
        git: GitRepository,
    ) -> None:
        """Receive the ports the flow needs.

        Args:
            cards: reads the cards and their progress.
            progress: where the branch is recorded.
            evaluator: to require that G4 passed.
            git: the local repository and its remote.
        """
        self._cards = cards
        self._progress = progress
        self._evaluator = evaluator
        self._git = git

    def execute(self, dossier_id: str) -> NextItemResult:
        """Create the branch of the first card that is not merged.

        Args:
            dossier_id: three-digit dossier id.

        Raises:
            GateOrderError: when G4 has not passed.
            ItemRefusedError: when nothing may change (every reason is listed); git is then
                left exactly as it was.
        """
        g4 = self._evaluator.one(dossier_id).status(GateId.G4)
        if g4.state is not GateState.PASSED:
            raise GateOrderError(f"cards are built after G4 passes; it is {g4.state}")
        stored = self._cards.progress(dossier_id)
        sections = self._cards.sections(dossier_id)
        pending = stored.unmerged(tuple(sections))
        if not pending:
            raise ItemRefusedError(("every card of the backlog is merged; nothing is next",))
        number = pending[0]
        problems = self._problems(stored.record(number)) + self._git_problems()
        if problems:
            raise ItemRefusedError(problems)
        title = self._cards.one(dossier_id, number).title
        branch = item_branch_name(dossier_id, number, title)
        deleted = self._sync_and_open(branch)
        updated = stored.with_branch(number, branch)
        if updated.record(number).state is ItemState.APPROVED:
            updated = updated.move(number, ItemState.BUILDING)
        self._progress.save(dossier_id, updated)
        return NextItemResult(number, branch, deleted)

    def _problems(self, record: ItemRecord) -> tuple[str, ...]:
        """Return why the card already in flight blocks starting another.

        Args:
            record: the first card that is not merged.
        """
        if record.state in _STARTED:
            return (
                f"card {record.number} is not merged (it is {record.state.value}); merge its "
                f"pull request, then run: sdd item merged <id> {record.number}",
            )
        return ()

    def _git_problems(self) -> tuple[str, ...]:
        """Return why git is not ready: remote, working tree, unmerged local branches."""
        if not self._git.fetch():
            return ("the remote cannot be reached; check the network and try again",)
        problems = []
        dirty = [p for p in self._git.dirty_paths() if not p.endswith("progress.yaml")]
        if dirty:
            shown = ", ".join(dirty[:5]) + (" ..." if len(dirty) > 5 else "")
            problems.append(f"the working tree has uncommitted changes: {shown}")
        for branch in self._git.local_branches():
            if branch != MAIN and not self._git.is_merged(branch, REMOTE_MAIN):
                problems.append(f"local branch {branch} is not merged into {REMOTE_MAIN}")
        return tuple(problems)

    def _sync_and_open(self, branch: str) -> tuple[str, ...]:
        """Switch to ``main``, fast-forward it, delete merged branches and create `branch`.

        Args:
            branch: the name of the new card branch.

        Raises:
            ItemRefusedError: when git refuses a step; later steps are not attempted.
        """
        if not self._git.switch(MAIN):
            raise ItemRefusedError((f"git could not switch to {MAIN}",))
        if not self._git.fast_forward(MAIN):
            raise ItemRefusedError((f"{MAIN} cannot be fast-forwarded to {REMOTE_MAIN}",))
        deleted = tuple(
            b
            for b in self._git.local_branches()
            if b != MAIN and self._git.delete_merged_branch(b)
        )
        if not self._git.create_branch(branch, MAIN):
            raise ItemRefusedError((f"git could not create branch {branch}",))
        return deleted


class MarkItemMerged:
    """Record a card as merged, but only when git shows its commit in ``origin/main``."""

    def __init__(
        self,
        cards: ItemCards,
        progress: ProgressRepository,
        git: GitRepository,
        clock: Clock,
    ) -> None:
        """Receive the ports the recording needs.

        Args:
            cards: reads the cards and their progress.
            progress: where the new state is saved.
            git: the local repository and its remote.
            clock: the merge time.
        """
        self._cards = cards
        self._progress = progress
        self._git = git
        self._clock = clock

    def execute(self, dossier_id: str, number: str) -> ItemRecord:
        """Mark card `number` as merged.

        Args:
            dossier_id: three-digit dossier id.
            number: the card number.

        Returns:
            The card's record after the change.

        Raises:
            UnknownItemError: when the backlog has no such card.
            ItemRefusedError: when the card is not verified, the remote is unreachable, no
                commit is known, or the commit is not in ``origin/main`` (the card is then
                left ``pr-open`` with its commit recorded).
        """
        self._cards.one(dossier_id, number)
        stored = self._cards.progress(dossier_id)
        record = stored.record(number)
        if record.state not in (ItemState.VERIFIED, ItemState.PR_OPEN):
            raise ItemRefusedError(
                (
                    f"card {number} is {record.state.value}; only a verified card can be merged "
                    f"(run: sdd item verify {dossier_id} {number})",
                )
            )
        if not self._git.fetch():
            raise ItemRefusedError(("the remote cannot be reached; check the network",))
        commit = record.commit or self._git.tip(record.branch)
        if not commit:
            raise ItemRefusedError(
                (f"no commit is recorded for card {number}, and its branch has no tip",)
            )
        opened = stored.opened(number, commit)
        if not self._git.contains(REMOTE_MAIN, commit):
            self._progress.save(dossier_id, opened)
            raise ItemRefusedError(
                (
                    f"commit {commit[:7]} is not in {REMOTE_MAIN} yet; merge the pull request "
                    "(a person does), then run this again",
                )
            )
        merged = opened.merged(number, self._clock.now())
        self._progress.save(dossier_id, merged)
        return merged.record(number)
