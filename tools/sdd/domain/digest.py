"""Content digests: the fingerprint an approval or a verification is bound to.

Domain layer. When we approve a gate, the harness stores the SHA-256 digest of the gate's
artifacts. If anyone (a person or an agent) edits those artifacts afterwards, the digest no
longer matches and the approval becomes *stale*: the agreement was about a text that no longer
exists (ADR-0003).

Two normalisations keep the digest about *meaning*, not about noise:

* line endings are unified (CRLF and CR become LF), so Windows and Linux checkouts agree;
* Markdown task boxes are reset (``- [x]`` becomes ``- [ ]``), so ticking a task in `tasks.md`
  during the build does not invalidate the approved plan.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

_TASK_BOX = re.compile(r"^(\s*[-*+]\s+)\[[ xX]\]", re.MULTILINE)
_PREFIX = "sha256:"


def normalise_text(text: str) -> str:
    """Return the canonical form of a text artifact used for digests.

    Args:
        text: the raw file content.

    Returns:
        The content with LF line endings, task boxes unticked, outer blank space trimmed and
        exactly one trailing newline.
    """
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    return _TASK_BOX.sub(r"\1[ ]", unified).strip() + "\n"


def digest_texts(named_texts: Iterable[tuple[str, str]]) -> str:
    """Digest a set of named text artifacts, independent of the order they are given in.

    Args:
        named_texts: pairs of (file name, content). The name is part of the digest so that
            moving content from one artifact to another is a change.

    Returns:
        A string of the form ``sha256:<64 hex digits>``.
    """
    hasher = hashlib.sha256()
    for name, text in sorted(named_texts):
        hasher.update(name.encode("utf-8") + b"\0")
        hasher.update(normalise_text(text).encode("utf-8") + b"\0")
    return _PREFIX + hasher.hexdigest()


def digest_files(named_bytes: Iterable[tuple[str, bytes]]) -> str:
    """Digest a set of files given as bytes (used for the governed code of gate G5).

    Args:
        named_bytes: pairs of (repository-relative path, raw content). CRLF is turned into LF
            so the same commit gives the same digest on every operating system.

    Returns:
        A string of the form ``sha256:<64 hex digits>``.
    """
    hasher = hashlib.sha256()
    for name, content in sorted(named_bytes):
        hasher.update(name.encode("utf-8") + b"\0")
        hasher.update(content.replace(b"\r\n", b"\n") + b"\0")
    return _PREFIX + hasher.hexdigest()


def short(digest: str) -> str:
    """Return a 12-character form of a digest for messages (never for comparisons).

    Args:
        digest: a value produced by `digest_texts` or `digest_files`.

    Returns:
        The first 12 hex digits.
    """
    return digest.removeprefix(_PREFIX)[:12]
