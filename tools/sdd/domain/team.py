"""The team: who "we" are and how many of us must approve a human gate.

Domain layer. Every human activity of the operating model (stakeholder, product owner, designer,
tech lead, QA) is played by the two of us, mentor and mentee. A human gate passes when the
approvals satisfy the team's `ApprovalPolicy`; the default policy is ``all``: both of us
(ADR-0003). The data lives in `harness/team.yaml`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from sdd.domain.errors import InvalidTeamError, UnknownMemberError


class ApprovalPolicy(StrEnum):
    """How many members must approve the current artifacts for a human gate to pass."""

    ALL = "all"
    """Every member (the default: decisions are joint)."""

    ANY = "any"
    """At least one member (useful when one of us is away; must be a deliberate choice)."""


@dataclass(frozen=True)
class TeamMember:
    """One person who can approve gates.

    Attributes:
        id: short handle used on the command line (``sdd approve ... --as mentor``).
        name: full name, for the audit trail and the documents.
        role: role in the mentorship, e.g. "mentor" or "mentee".
    """

    id: str
    name: str
    role: str


@dataclass(frozen=True)
class Team:
    """The approvers of this repository and the policy that turns approvals into a decision.

    Attributes:
        members: at least one member, ids unique.
        policy: the approval policy applied to every human gate.
    """

    members: tuple[TeamMember, ...]
    policy: ApprovalPolicy = ApprovalPolicy.ALL

    def __post_init__(self) -> None:
        """Reject an empty team or duplicated ids, which would make approvals ambiguous.

        Raises:
            InvalidTeamError: when the invariant is broken.
        """
        ids = [member.id for member in self.members]
        if not ids:
            raise InvalidTeamError("the team needs at least one member")
        if len(ids) != len(set(ids)):
            raise InvalidTeamError(f"duplicated member ids in {ids}")

    def member(self, member_id: str) -> TeamMember:
        """Return the member with this id.

        Args:
            member_id: the handle given on the command line.

        Returns:
            The member.

        Raises:
            UnknownMemberError: when nobody in the team has that id.
        """
        for member in self.members:
            if member.id == member_id:
                return member
        known = ", ".join(m.id for m in self.members)
        raise UnknownMemberError(f"{member_id!r} is not in harness/team.yaml (known: {known})")

    def missing_approvers(self, approver_ids: Iterable[str]) -> tuple[str, ...]:
        """Return the members whose approval is still needed under the policy.

        Args:
            approver_ids: ids of the members who approved the *current* artifacts.

        Returns:
            Empty when the gate's human condition is satisfied; otherwise the ids still needed
            (for ``any``, every member, since any one of them would do).
        """
        approved = set(approver_ids)
        if self.policy is ApprovalPolicy.ANY:
            return () if approved else tuple(m.id for m in self.members)
        return tuple(m.id for m in self.members if m.id not in approved)
