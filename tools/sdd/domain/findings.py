"""Findings: what a check of the harness reports.

Domain layer. Every rule that inspects the repository (dossier consistency, documentation lint,
generated-file drift, the commit guard) reports `Finding` values. An ``error`` blocks the commit
(`sdd check` exits non-zero); a ``warning`` is shown but does not block.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """How serious a finding is."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    """One problem found by a rule.

    Attributes:
        rule: short id of the rule that found it (e.g. "mermaid-logo", "stale-approval").
        severity: error or warning.
        message: what is wrong and, when possible, how to fix it.
        location: repository-relative path, optionally ``path:line``; empty when global.
    """

    rule: str
    severity: Severity
    message: str
    location: str = ""


def has_errors(findings: Iterable[Finding]) -> bool:
    """Return true when at least one finding is an error.

    Args:
        findings: the findings of one or more rules.
    """
    return any(finding.severity is Severity.ERROR for finding in findings)
