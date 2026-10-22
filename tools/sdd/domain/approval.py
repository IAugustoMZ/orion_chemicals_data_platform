"""Approvals and verifications: the evidence that closes a gate.

Domain layer. An `Approval` is one person's "yes" to the artifacts of a human gate, bound to the
digest of those artifacts at that moment. A `Verification` is the machine's result for gate G5,
bound to the digest of the governed code. Both are value objects: they are never edited, only
replaced by a newer one (which is how the audit trail of `dossier.yaml` stays honest, RT38).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Approval:
    """One team member's approval of a human gate.

    Attributes:
        member: id of the approving member (see `harness/team.yaml`).
        approved_at: when it was recorded (timezone-aware, UTC).
        digest: digest of the gate's artifacts that were approved (`digest.digest_texts`).
        git_identity: ``user.name <user.email>`` from git at approval time, for the audit trail.
        note: optional reason or remark typed by the approver.
    """

    member: str
    approved_at: datetime
    digest: str
    git_identity: str
    note: str = ""


@dataclass(frozen=True)
class CheckOutcome:
    """Result of one deterministic check of the quality suite.

    Attributes:
        check_id: id of the check in `harness/checks.yaml` (e.g. "lint", "tests").
        passed: true when the command exited with status 0.
        summary: the last lines of the command's output, enough to see why it failed.
    """

    check_id: str
    passed: bool
    summary: str


@dataclass(frozen=True)
class Verification:
    """The machine's verdict for gate G5 (Build: deterministic checks passed).

    Attributes:
        verified_at: when the suite ran (timezone-aware, UTC).
        digest: digest of every governed file when the suite finished.
        commit: the git commit checked out (``HEAD``), for orientation only.
        results: one outcome per check, in suite order.
    """

    verified_at: datetime
    digest: str
    commit: str
    results: tuple[CheckOutcome, ...]

    @property
    def passed(self) -> bool:
        """Return true when every check of the suite passed (and at least one ran)."""
        return bool(self.results) and all(result.passed for result in self.results)

    @property
    def failed_checks(self) -> tuple[str, ...]:
        """Return the ids of the checks that failed, in suite order."""
        return tuple(result.check_id for result in self.results if not result.passed)
