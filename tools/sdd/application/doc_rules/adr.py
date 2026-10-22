"""Rule: Architecture Decision Records are well formed and all listed in the index.

Application layer. ADRs live in `docs/architecture/decisions/NNNN-title.md`. Each must carry a
``- **Status:**`` and a ``- **Date:**`` line, numbers are never reused, and the folder's
`README.md` must link every ADR so that a reader finds them all (documentation-standard.md).
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable

from sdd.application.ports.documents import Document, DocumentStore
from sdd.domain.findings import Finding, Severity

_ADR_NAME = re.compile(r"^(?P<number>\d{4})-[a-z0-9-]+\.md$")
_REQUIRED_LINES = ("- **Status:**", "- **Date:**")


class AdrRule:
    """Check each ADR's header and, on the index page, that every ADR is listed once."""

    def __init__(self, store: DocumentStore, decisions_dir: str) -> None:
        """Receive the store and where the ADRs live.

        Args:
            store: the repository's files.
            decisions_dir: repository-relative folder of the ADRs (no trailing slash).
        """
        self._store = store
        self._dir = decisions_dir

    def check(self, document: Document) -> Iterable[Finding]:
        """Check an ADR file, or the index when `document` is the folder's README.

        Args:
            document: the Markdown document.
        """
        folder, name = posixpath.split(document.path)
        if folder != self._dir:
            return
        if name == "README.md":
            yield from self._check_index(document)
        elif _ADR_NAME.match(name):
            for required in _REQUIRED_LINES:
                if required not in document.text:
                    yield Finding(
                        "adr-format", Severity.ERROR, f"missing '{required}' line", document.path
                    )

    def _check_index(self, index: Document) -> Iterable[Finding]:
        """Report ADRs missing from the index and numbers used twice.

        Args:
            index: the decisions README.
        """
        seen: dict[str, str] = {}
        for path in self._store.paths(prefix=f"{self._dir}/", suffix=".md"):
            name = posixpath.basename(path)
            match = _ADR_NAME.match(name)
            if not match:
                continue
            number = match.group("number")
            if number in seen:
                yield Finding(
                    "adr-number", Severity.ERROR, f"ADR {number} used by {seen[number]}", path
                )
            seen[number] = name
            if f"({name})" not in index.text:
                yield Finding(
                    "adr-index", Severity.ERROR, f"{name} is not linked from the index", index.path
                )
