"""Adapter of the `CheckRunner` port: run a quality check as a subprocess.

Infrastructure layer. Commands come from `harness/checks.yaml` (a governed file), are resolved
with `shutil.which` (so ``ruff`` finds ``ruff.exe`` on Windows inside the Poetry environment) and
run without a shell. The summary keeps the last lines of output, enough to see why a check
failed without flooding `dossier.yaml`.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 # running the quality suite is the purpose of this adapter
from collections.abc import Callable
from pathlib import Path

from sdd.domain.approval import CheckOutcome
from sdd.domain.quality import QualityCheck

_SUMMARY_LINES = 6
_TIMEOUT_SECONDS = 900
_MAX_FILE_CHARS = 20_000


class SubprocessCheckRunner:
    """Run each check's command in the repository root."""

    def __init__(self, root: Path, lister: Callable[[Path], tuple[str, ...]]) -> None:
        """Remember the root and how to list files for checks with ``pass_files``.

        Args:
            root: absolute path of the repository root.
            lister: returns the repository's files (`git.listed_files`).
        """
        self._root = root
        self._lister = lister

    def run(self, check: QualityCheck) -> CheckOutcome:
        """Run the check and report the outcome.

        Args:
            check: the check to run. With ``pass_files``, the files are split into batches that
                keep each command line under `_MAX_FILE_CHARS` (Windows caps a command line at
                about 32,000 characters); the check passes only if every batch passes.
        """
        executable = shutil.which(check.command[0])
        if executable is None:
            return CheckOutcome(check.id, False, f"command not found: {check.command[0]}")
        base = [executable, *check.command[1:]]
        batches = _batches(self._lister(self._root)) if check.pass_files else [[]]
        for batch in batches:
            passed, summary = self._run_once([*base, *batch])
            if not passed:
                return CheckOutcome(check.id, False, summary)
        return CheckOutcome(check.id, True, summary)

    def _run_once(self, arguments: list[str]) -> tuple[bool, str]:
        """Run one command line and return (passed, output summary).

        Args:
            arguments: the resolved executable followed by its arguments.
        """
        try:
            completed = subprocess.run(  # noqa: S603  # nosec B603 # governed argv, no shell
                arguments,
                cwd=self._root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, f"timed out after {_TIMEOUT_SECONDS} s"
        output = (completed.stdout + completed.stderr).strip().splitlines()
        return completed.returncode == 0, "\n".join(output[-_SUMMARY_LINES:]) or "(no output)"


def _batches(files: tuple[str, ...]) -> list[list[str]]:
    """Split file names into lists whose joined length stays under `_MAX_FILE_CHARS`.

    Args:
        files: repository-relative paths.

    Returns:
        At least one list (possibly empty), preserving order.
    """
    batches: list[list[str]] = [[]]
    length = 0
    for name in files:
        if batches[-1] and length + len(name) + 1 > _MAX_FILE_CHARS:
            batches.append([])
            length = 0
        batches[-1].append(name)
        length += len(name) + 1
    return batches
