"""Use case: run every documentation rule over every Markdown file of the repository.

Application layer. Part of `sdd check`, so it runs in pre-commit and in the G5 suite. Generated
copies (the tool adapters under `.claude/`, `.cursor/`, `.github/`) and templates are excluded:
their source is checked instead, and templates contain placeholders on purpose.
"""

from __future__ import annotations

from collections.abc import Sequence

from sdd.application.doc_rules import DocumentRule
from sdd.application.ports.documents import Document, DocumentStore
from sdd.domain.findings import Finding


class LintDocs:
    """Apply a list of `DocumentRule` strategies to the repository's Markdown files."""

    def __init__(
        self, store: DocumentStore, rules: Sequence[DocumentRule], excluded: tuple[str, ...]
    ) -> None:
        """Receive the store, the rules and the path prefixes to skip.

        Args:
            store: the repository's files.
            rules: the rules, applied in order.
            excluded: path prefixes that are not linted.
        """
        self._store = store
        self._rules = tuple(rules)
        self._excluded = excluded

    def execute(self) -> tuple[Finding, ...]:
        """Return the findings of every rule on every linted document."""
        findings: list[Finding] = []
        for path in self._store.paths(suffix=".md"):
            if path.startswith(self._excluded):
                continue
            document = Document(path, self._store.read(path) or "")
            for rule in self._rules:
                findings.extend(rule.check(document))
        return tuple(findings)
