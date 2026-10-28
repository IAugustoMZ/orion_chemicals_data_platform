"""Adapter of the `Workspace` port, backed by git and the working tree.

Infrastructure layer. The governed digest hashes every governed file (as defined in
`sdd.domain.governance`) that git knows about or would add, so files ignored by `.gitignore`
(virtual environments, caches) never influence gate G5.
"""

from __future__ import annotations

from pathlib import Path

from sdd.domain.digest import digest_files
from sdd.domain.governance import is_governed
from sdd.infrastructure.git import listed_files, run_git


class GitWorkspace:
    """Answer questions about the git working copy at `root`."""

    def __init__(self, root: Path) -> None:
        """Remember the repository root.

        Args:
            root: absolute path of the repository root.
        """
        self._root = root

    def current_branch(self) -> str:
        """Return the checked-out branch, or "" when HEAD is detached."""
        return run_git(self._root, "branch", "--show-current") or ""

    def git_identity(self) -> str:
        """Return ``name <email>`` from git config, or a note when it is not configured."""
        name = run_git(self._root, "config", "user.name")
        email = run_git(self._root, "config", "user.email")
        if not name and not email:
            return "(git identity not configured)"
        return f"{name or '?'} <{email or '?'}>"

    def head_commit(self) -> str:
        """Return the abbreviated HEAD commit, or "(no commit)"."""
        return run_git(self._root, "rev-parse", "--short", "HEAD") or "(no commit)"

    def governed_digest(self) -> str:
        """Return the digest of every governed file currently in the working tree."""
        files = ((p, (self._root / p).read_bytes()) for p in listed_files(self._root))
        return digest_files((path, data) for path, data in files if is_governed(path))
