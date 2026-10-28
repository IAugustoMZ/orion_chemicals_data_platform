"""Ports for the environment the harness runs in: git, the terminal, the clock, processes.

Application layer. These are the "impure" parts of every use case. Keeping them behind
Protocols is what lets the tests replace git with a fixed branch name, the terminal with a
scripted answer and the clock with a fixed instant.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sdd.domain.approval import CheckOutcome
from sdd.domain.quality import QualityCheck


class Workspace(Protocol):
    """Facts about the git working copy."""

    def current_branch(self) -> str:
        """Return the checked-out branch name (empty when detached)."""
        ...

    def git_identity(self) -> str:
        """Return ``user.name <user.email>``, or an explanatory text when not configured."""
        ...

    def head_commit(self) -> str:
        """Return the abbreviated ``HEAD`` commit, or "(no commit)" in a new repository."""
        ...

    def governed_digest(self) -> str:
        """Return the digest of every governed file as it is on disk now."""
        ...


class HumanConfirmation(Protocol):
    """Ask the person at the terminal to confirm an approval."""

    def confirm(self, summary: str, expected: str) -> bool:
        """Show `summary` and return true only if the person types `expected`.

        Raises:
            HumanConfirmationRequiredError: when no interactive terminal is attached
                (which is the case for coding agents, ADR-0003).
        """
        ...


class Clock(Protocol):
    """The current time."""

    def now(self) -> datetime:
        """Return the current instant, timezone-aware, in UTC."""
        ...


class CheckRunner(Protocol):
    """Run one deterministic check."""

    def run(self, check: QualityCheck) -> CheckOutcome:
        """Run the check's command and report whether it passed, with an output summary."""
        ...
