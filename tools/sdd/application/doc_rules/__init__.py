"""Documentation rules: the mechanical part of `harness/documentation-standard.md`.

Each rule is a small class with one method, `check(document) -> findings` (strategy pattern):
`LintDocs` runs every rule on every Markdown file, and adding a rule never changes the rules that
exist (open/closed principle).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from sdd.application.ports.documents import Document
from sdd.domain.findings import Finding


class DocumentRule(Protocol):
    """A check applied to one Markdown document."""

    def check(self, document: Document) -> Iterable[Finding]:
        """Return the findings of this rule for `document` (empty when it complies)."""
        ...
