"""Adapter of the `HumanConfirmation` port: ask the person at an interactive terminal.

Infrastructure layer. This is the reason a coding agent cannot approve a gate (ADR-0003): agents
run commands with no terminal attached to standard input, so `isatty()` is false and the
approval is refused before anything is asked. Piping an answer in (``echo y | ...``) fails for
the same reason. A pseudo-terminal wrapper can still create a terminal, so this is a safeguard
against an agent approving by mistake, not against deliberate circumvention; the agent guard
(which blocks `sdd approve` in agent commands) and the audit trail cover the rest. The answer
itself is a plain ``y/N`` question (ADR-0016): the safeguard is the terminal, not a typed phrase.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO

from sdd.domain.errors import HumanConfirmationRequiredError

_YES = frozenset({"y", "yes"})


class TerminalConfirmation:
    """Show a summary and ask the person ``Approve? [y/N]``; only ``y`` or ``yes`` approves."""

    def __init__(
        self,
        stdin: TextIO | None = None,
        prompt: Callable[[str], str] = input,
        echo: Callable[[str], None] = print,
    ) -> None:
        """Receive the terminal streams (injectable for tests).

        Args:
            stdin: the input stream whose `isatty()` is checked (default: `sys.stdin`).
            prompt: reads one line after showing a prompt (default: `input`).
            echo: shows a line (default: `print`).
        """
        self._stdin = stdin
        self._prompt = prompt
        self._echo = echo

    def confirm(self, summary: str) -> bool:
        """Show `summary` and return true only if the person answers ``y`` or ``yes``.

        Case and surrounding spaces are ignored. Enter, ``n`` and anything else cancel.

        Args:
            summary: what is being approved (dossier, gate, artifacts, digest, approver).

        Raises:
            HumanConfirmationRequiredError: when standard input is not an interactive terminal.
        """
        stream = self._stdin or sys.stdin
        if stream is None or not stream.isatty():
            raise HumanConfirmationRequiredError(
                "approvals need a person at an interactive terminal; run `poetry run sdd "
                "approve ...` yourself (agents must ask us instead, AGENTS.md)"
            )
        self._echo(summary)
        self._echo("")
        try:
            answer = self._prompt("Approve? [y/N]: ")
        except EOFError:  # Ctrl-D (Ctrl-Z on Windows) closes the input: that is a "no"
            return False
        return answer.strip().lower() in _YES
