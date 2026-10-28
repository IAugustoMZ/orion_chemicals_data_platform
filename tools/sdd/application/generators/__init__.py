"""Generators: documents derived from the dossiers and the canonical harness sources.

Application layer. A document that can be computed must never be maintained by hand, or it
drifts. Each generator returns the files it owns as `GeneratedFile` values; `SyncGenerated`
writes them (`sdd sync`) or reports drift (`sdd check`). Generation is deterministic (no
timestamps), so regenerating an unchanged repository changes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeneratedFile:
    """One file, or one marked block inside a file, produced by a generator.

    Attributes:
        path: repository-relative path.
        content: the full file content, or the block's content when `block` is set.
        block: name of the block between ``<!-- sdd:<block>:start -->`` and
            ``<!-- sdd:<block>:end -->`` that the content replaces; None for whole files.
    """

    path: str
    content: str
    block: str | None = None


class Generator(Protocol):
    """Produces generated files."""

    def generate(self) -> tuple[GeneratedFile, ...]:
        """Return every file (or block) this generator owns, with its expected content."""
        ...

    def owned_prefixes(self) -> tuple[str, ...]:
        """Return folders whose every file belongs to this generator (orphans get removed)."""
        ...
