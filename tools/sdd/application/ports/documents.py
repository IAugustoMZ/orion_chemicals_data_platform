"""Ports for the repository's documents and templates.

Application layer. The documentation lint, the generators and the dossier creation read and
write text files through these Protocols, never through `open()`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Document:
    """A text file of the repository.

    Attributes:
        path: repository-relative path with forward slashes.
        text: the file's content.
    """

    path: str
    text: str


class DocumentStore(Protocol):
    """Read and write the repository's text files (tracked or new, never git-ignored)."""

    def paths(self, prefix: str = "", suffix: str = "") -> tuple[str, ...]:
        """Return the sorted paths that start with `prefix` and end with `suffix`."""
        ...

    def read(self, path: str) -> str | None:
        """Return the file's content, or None when it does not exist."""
        ...

    def write(self, path: str, content: str) -> None:
        """Write the file (UTF-8, LF line endings), creating parent folders."""
        ...

    def exists(self, path: str) -> bool:
        """Return true when the file or directory exists."""
        ...

    def remove(self, path: str) -> None:
        """Delete the file (used only for orphans in generated folders)."""
        ...


class TemplateLibrary(Protocol):
    """The artifact templates of `harness/templates/`."""

    def text(self, name: str) -> str:
        """Return the raw template, e.g. for `prd.md` (used to derive required sections)."""
        ...

    def render(self, name: str, values: Mapping[str, str]) -> str:
        """Return the template with every ``{{key}}`` replaced by ``values[key]``."""
        ...
