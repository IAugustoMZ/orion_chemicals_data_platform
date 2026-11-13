"""Adapter of the `GitRepository` port, backed by the ``git`` executable.

Infrastructure layer. Safe by construction (ADR-0023): every call passes `ensure_allowed`, which
refuses force, hard branch deletion and anything that pushes, so even a bug upstream cannot
rewrite history or publish. Merging a pull request is not here at all: a person does it.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from sdd.domain.errors import ForbiddenGitCommandError
from sdd.infrastructure.git import run_git

_FORBIDDEN_FLAGS = frozenset({"-D", "-f", "--force", "--force-with-lease", "--delete"})
_FORBIDDEN_COMMANDS = frozenset({"push", "reset", "clean"})
_REMOTE = "origin"


def ensure_allowed(args: Sequence[str]) -> None:
    """Refuse git arguments the harness must never run.

    Args:
        args: the arguments after ``git``.

    Raises:
        ForbiddenGitCommandError: for force flags, ``branch -D``, push, reset and clean.
    """
    if args and args[0] in _FORBIDDEN_COMMANDS:
        raise ForbiddenGitCommandError(f"git {args[0]} is never run by the harness")
    bad = _FORBIDDEN_FLAGS.intersection(args)
    if bad:
        raise ForbiddenGitCommandError(f"git flag {sorted(bad)[0]} is never run by the harness")


class GitCliRepository:
    """Run the git operations of the per-card flow in the repository at `root`."""

    def __init__(self, root: Path) -> None:
        """Remember the repository root.

        Args:
            root: absolute path of the repository root.
        """
        self._root = root

    def fetch(self) -> bool:
        """Refresh ``origin``; false when git failed (for instance, no network)."""
        return self._git("fetch", "--prune", _REMOTE) is not None

    def dirty_paths(self) -> tuple[str, ...]:
        """Return the paths with uncommitted changes, including untracked files."""
        output = self._git("status", "--porcelain") or ""
        return tuple(line[3:].split(" -> ")[-1] for line in output.splitlines() if line)

    def current_branch(self) -> str:
        """Return the checked-out branch, or "" when detached."""
        return self._git("branch", "--show-current") or ""

    def local_branches(self) -> tuple[str, ...]:
        """Return every local branch name."""
        output = self._git("for-each-ref", "--format=%(refname:short)", "refs/heads") or ""
        return tuple(sorted(output.splitlines()))

    def is_merged(self, branch: str, into: str) -> bool:
        """Return whether `branch` is an ancestor of `into`.

        Args:
            branch: a local branch name.
            into: a ref such as ``origin/main``.
        """
        return self._git("merge-base", "--is-ancestor", branch, into) is not None

    def switch(self, branch: str) -> bool:
        """Check out an existing local branch.

        Args:
            branch: the branch to check out.
        """
        return self._git("switch", branch) is not None

    def fast_forward(self, branch: str) -> bool:
        """Fast-forward the checked-out branch to ``origin/<branch>``, never merging.

        Args:
            branch: the checked-out branch.
        """
        return self._git("merge", "--ff-only", f"{_REMOTE}/{branch}") is not None

    def delete_merged_branch(self, branch: str) -> bool:
        """Delete a branch with ``git branch -d``, which git itself refuses if it is unmerged.

        Args:
            branch: the branch to delete.
        """
        return self._git("branch", "-d", branch) is not None

    def create_branch(self, name: str, start: str) -> bool:
        """Create `name` at `start` and check it out.

        Args:
            name: the new branch name.
            start: the ref it starts from.
        """
        return self._git("switch", "-c", name, start) is not None

    def tip(self, ref: str) -> str:
        """Return the full commit id of `ref`, or "" when it does not exist.

        Args:
            ref: a branch or other ref.
        """
        return self._git("rev-parse", "--verify", "--quiet", ref) or ""

    def contains(self, ref: str, commit: str) -> bool:
        """Return whether `commit` is in the history of `ref`.

        Args:
            ref: e.g. ``origin/main``.
            commit: a commit id.
        """
        return self._git("merge-base", "--is-ancestor", commit, ref) is not None

    def _git(self, *args: str) -> str | None:
        """Run an allowed git command in the repository.

        Args:
            *args: git arguments.

        Raises:
            ForbiddenGitCommandError: when the arguments are on the forbidden list.
        """
        ensure_allowed(args)
        return run_git(self._root, *args)
