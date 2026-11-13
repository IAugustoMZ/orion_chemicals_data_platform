"""The progress of a dossier's backlog, card by card (ADR-0023).

Domain layer. A card moves through `ItemState` in one direction, with a few allowed steps back
when its text changes or its work is reopened. The records are immutable: every change returns a
new `ItemProgress`, so the file the infrastructure writes is always a consistent snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from sdd.domain.approval import Approval
from sdd.domain.errors import IllegalTransitionError


class ItemState(StrEnum):
    """Where a card is in its own life."""

    OUTLINE = "outline"
    REFINED = "refined"
    APPROVED = "approved"
    BUILDING = "building"
    VERIFIED = "verified"
    PR_OPEN = "pr-open"
    MERGED = "merged"


_ALLOWED: Mapping[ItemState, frozenset[ItemState]] = {
    ItemState.OUTLINE: frozenset({ItemState.REFINED}),
    ItemState.REFINED: frozenset({ItemState.APPROVED}),
    ItemState.APPROVED: frozenset({ItemState.BUILDING, ItemState.VERIFIED, ItemState.REFINED}),
    ItemState.BUILDING: frozenset({ItemState.VERIFIED, ItemState.REFINED}),
    ItemState.VERIFIED: frozenset({ItemState.PR_OPEN, ItemState.BUILDING, ItemState.REFINED}),
    ItemState.PR_OPEN: frozenset({ItemState.MERGED, ItemState.BUILDING}),
    ItemState.MERGED: frozenset(),
}
"""The state machine: the steps a card may take from each state."""


@dataclass(frozen=True)
class ItemRecord:
    """What is recorded about one card.

    Attributes:
        number: the card number, ``"01"``.
        state: the stored state.
        approvals: the latest approval of each member, bound to a card digest.
        branch: the card's git branch, once created.
        commit: the commit the pull request was opened from, once known.
        pull_request: the pull request reference, once opened.
        merged_at: when the merge was recorded.
    """

    number: str
    state: ItemState = ItemState.OUTLINE
    approvals: tuple[Approval, ...] = ()
    branch: str = ""
    commit: str = ""
    pull_request: str = ""
    merged_at: datetime | None = None

    def fresh_approvers(self, digest: str) -> tuple[str, ...]:
        """Return the members whose approval matches the card as it is now.

        Args:
            digest: the current digest of the card's section.
        """
        return tuple(a.member for a in self.approvals if a.digest == digest)


@dataclass(frozen=True)
class ItemProgress:
    """The records of every card that has one; a card without a record is an outline.

    Attributes:
        items: record by card number.
        version: format version of the stored file.
    """

    items: Mapping[str, ItemRecord] = field(default_factory=dict)
    version: int = 1

    def record(self, number: str) -> ItemRecord:
        """Return the record of a card, or an empty outline record.

        Args:
            number: the card number.
        """
        return self.items.get(number, ItemRecord(number))

    def with_approval(self, number: str, approval: Approval, complete: bool) -> ItemProgress:
        """Record an approval, replacing the member's earlier one.

        Args:
            number: the card number.
            approval: the new approval.
            complete: whether the team policy is now satisfied for the card's current digest.

        Returns:
            A new progress. A card still in outline or refined becomes ``refined`` and, when
            `complete`, ``approved``; a card further on keeps its state.
        """
        current = self.record(number)
        kept = tuple(a for a in current.approvals if a.member != approval.member)
        state = current.state
        if state is ItemState.OUTLINE:
            state = ItemState.REFINED
        if complete and state is ItemState.REFINED:
            state = ItemState.APPROVED
        return self._with(replace(current, approvals=(*kept, approval), state=state))

    def move(self, number: str, target: ItemState) -> ItemProgress:
        """Move a card to another state.

        Args:
            number: the card number.
            target: the state to reach.

        Raises:
            IllegalTransitionError: when the state machine does not allow the step.
        """
        current = self.record(number)
        if target is current.state:
            return self
        if target not in _ALLOWED[current.state]:
            raise IllegalTransitionError(
                f"card {number} cannot go from {current.state.value} to {target.value}"
            )
        return self._with(replace(current, state=target))

    def unmerged(self, numbers: tuple[str, ...]) -> tuple[str, ...]:
        """Return the cards among `numbers` that are not merged yet.

        Args:
            numbers: the card numbers of the backlog.
        """
        return tuple(n for n in numbers if self.record(n).state is not ItemState.MERGED)

    def _with(self, record: ItemRecord) -> ItemProgress:
        """Return a copy holding `record`.

        Args:
            record: the new record of its card.
        """
        return replace(self, items={**self.items, record.number: record})
