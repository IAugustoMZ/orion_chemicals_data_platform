"""Adapter of the `DocumentStore` port, backed by the working tree.

Infrastructure layer. The list of files comes from git (tracked plus new, never ignored), so the
documentation lint and the generators see exactly what a commit would contain. Files are read
and written as UTF-8 with LF line endings (see `.gitattributes`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path


class FileDocumentStore:
    """Read and write text files under the repository root."""

    def __init__(self, root: Path, lister: Callable[[Path], tuple[str, ...]]) -> None:
        """Remember the root and how to list the repository's files.

        Args:
            root: absolute path of the repository root.
            lister: returns the repository-relative file paths (`git.listed_files`).
        """
        self._root = root
        self._lister = lister
        self._cache: tuple[str, ...] | None = None

    def paths(self, prefix: str = "", suffix: str = "") -> tuple[str, ...]:
        """Return the sorted paths that start with `prefix` and end with `suffix`.

        Args:
            prefix: repository-relative path prefix, e.g. ".agents/skills/".
            suffix: file ending, e.g. ".md".
        """
        if self._cache is None:
            self._cache = self._lister(self._root)
        return tuple(p for p in self._cache if p.startswith(prefix) and p.endswith(suffix))

    def read(self, path: str) -> str | None:
        """Return the file's text, or None when it does not exist.

        Args:
            path: repository-relative path.
        """
        file = self._root / path
        if not file.is_file():
            return None
        return file.read_text(encoding="utf-8").replace("\r\n", "\n")

    def write(self, path: str, content: str) -> None:
        """Write the file as UTF-8 with LF endings, creating its folders.

        Args:
            path: repository-relative path.
            content: the full content.
        """
        file = self._root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8", newline="\n")
        self._cache = None

    def exists(self, path: str) -> bool:
        """Return true when the file or folder exists under the root.

        Args:
            path: repository-relative path (may be "." for the root).
        """
        return (self._root / path).exists()

    def remove(self, path: str) -> None:
        """Delete the file if it exists.

        Args:
            path: repository-relative path.
        """
        (self._root / path).unlink(missing_ok=True)
        self._cache = None
