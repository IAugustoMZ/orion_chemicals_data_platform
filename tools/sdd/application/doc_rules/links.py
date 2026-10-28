"""Rule: every relative link in a Markdown document points to a file that exists.

Application layer. Broken links are the first sign that documentation drifts from the code.
External links (http, https, mailto) and pure anchors are not checked: the site build
(`mkdocs build --strict`, a G5 check) covers anchors, and external sites are outside our control.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable

from sdd.application.doc_rules.markdown import prose_lines
from sdd.application.ports.documents import Document, DocumentStore
from sdd.domain.findings import Finding, Severity

_LINK = re.compile(r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)")
_EXTERNAL = ("http://", "https://", "mailto:", "#", "data:")


class LocalLinkRule:
    """Report relative links whose target is missing."""

    def __init__(self, store: DocumentStore) -> None:
        """Receive the store used to test whether a target exists.

        Args:
            store: the repository's files.
        """
        self._store = store

    def check(self, document: Document) -> Iterable[Finding]:
        """Report every broken relative link of the document.

        Args:
            document: the Markdown document.
        """
        folder = posixpath.dirname(document.path)
        for number, line in prose_lines(document.text):
            for match in _LINK.finditer(line):
                target = match.group("target").strip("<>")
                if target.startswith(_EXTERNAL) or "{{" in target:
                    continue
                path = posixpath.normpath(posixpath.join(folder, target.split("#")[0]))
                if not self._store.exists(path):
                    yield Finding(
                        "broken-link",
                        Severity.ERROR,
                        f"link target {target!r} does not exist",
                        f"{document.path}:{number}",
                    )
