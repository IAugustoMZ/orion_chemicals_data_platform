"""Port for the git repository operations the per-card flow needs (ADR-0023).

Application layer. The port is deliberately small and *safe by construction*: it has no way to
force-push, hard-delete a branch or merge a pull request. A person merges; the harness only
reads the result and tidies up what git itself confirms is merged.
"""

from __future__ import annotations

from typing import Protocol


class GitRepository(Protocol):
    """The local repository and its remote ``origin``."""

    def fetch(self) -> bool:
        """Refresh the remote-tracking branches; return false when the remote is unreachable."""
        ...

    def dirty_paths(self) -> tuple[str, ...]:
        """Return the paths with uncommitted changes (modified, staged or untracked)."""
        ...

    def current_branch(self) -> str:
        """Return the checked-out branch (empty when detached)."""
        ...

    def local_branches(self) -> tuple[str, ...]:
        """Return the names of every local branch."""
        ...

    def is_merged(self, branch: str, into: str) -> bool:
        """Return whether every commit of `branch` is already in `into`.

        Args:
            branch: a local branch name.
            into: a ref such as ``origin/main``.
        """
        ...

    def switch(self, branch: str) -> bool:
        """Check out an existing local branch; return false when git refused.

        Args:
            branch: the branch to check out.
        """
        ...

    def fast_forward(self, branch: str) -> bool:
        """Fast-forward the checked-out `branch` to ``origin/<branch>``; false if it cannot.

        Args:
            branch: the checked-out branch.
        """
        ...

    def delete_merged_branch(self, branch: str) -> bool:
        """Delete a local branch only if git considers it merged (``git branch -d``).

        Args:
            branch: the branch to delete.
        """
        ...

    def create_branch(self, name: str, start: str) -> bool:
        """Create a branch at `start` and check it out; return false when git refused.

        Args:
            name: the new branch name.
            start: the ref it starts from, e.g. ``main``.
        """
        ...

    def tip(self, ref: str) -> str:
        """Return the full commit id `ref` points to, or "" when it does not exist.

        Args:
            ref: a branch or other ref.
        """
        ...

    def contains(self, ref: str, commit: str) -> bool:
        """Return whether `commit` is part of the history of `ref`.

        Args:
            ref: e.g. ``origin/main``.
            commit: a commit id.
        """
        ...
