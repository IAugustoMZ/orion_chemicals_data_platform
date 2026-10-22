"""The deterministic quality suite that closes gate G5.

Domain layer. A `QualityCheck` is a command that answers "yes" or "no" about the code with no
judgement involved (formatting, lint, types, layer contracts, tests, security scans, harness
consistency). The list lives in `harness/checks.yaml` so that adding a check is a data change,
not a code change (open/closed principle).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityCheck:
    """One command of the quality suite.

    Attributes:
        id: short unique id, used in reports and in `dossier.yaml`.
        title: what the check proves, for people.
        command: the program and its arguments, run without a shell (no injection surface).
        pass_files: when true, the repository's tracked files are appended to the command
            (needed by tools such as `detect-secrets-hook` that check a list of files).
    """

    id: str
    title: str
    command: tuple[str, ...]
    pass_files: bool = False
