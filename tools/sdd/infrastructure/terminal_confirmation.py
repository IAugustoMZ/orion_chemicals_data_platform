"""Adapter of the `HumanConfirmation` port: ask the person at an interactive terminal.

Infrastructure layer. This is the reason a coding agent cannot approve a gate (ADR-0003): agents
run commands with no terminal attached to standard input, so `isatty()` is false and the
approval is refused before anything is asked. Piping text in (``echo 001 G4 | sdd approve``)
fails for the same reason. It is a strong safeguard against an agent approving by mistake, not
against a person deliberately cheating; that is what the audit trail is for.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO

from sdd.domain.errors import HumanConfirmationRequiredError


class TerminalConfirmation:
    """Show a summary and require the person to type the expected text."""

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

    def confirm(self, summary: str, expected: str) -> bool:
        """Show `summary` and return true only if the person types `expected` exactly.

        Args:
            summary: what is being approved (dossier, gate, artifacts, digest, approver).
            expected: the text to type, e.g. "001 G4".

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
        answer = self._prompt(f"Type '{expected}' to approve (anything else cancels): ")
        return answer.strip() == expected
