"""Thin wrapper around the `git` executable, shared by the git-based adapters.

Infrastructure layer. Git is called with an argument list and no shell, so nothing typed by a
user can be interpreted as a command (bandit B603 is acknowledged below for that reason).
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 # required to call git; see run_git for the safeguards
from pathlib import Path


def run_git(root: Path, *args: str) -> str | None:
    """Run ``git <args>`` in `root` and return its standard output.

    Args:
        root: the repository root, used as working directory.
        *args: git arguments, e.g. ("branch", "--show-current").

    Returns:
        The output without the trailing newline, or None when git is missing or the command
        failed (for instance `git config user.name` when it is not configured).
    """
    executable = shutil.which("git")
    if executable is None:
        return None
    completed = subprocess.run(  # noqa: S603  # nosec B603 # fixed executable, no shell
        [executable, *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return completed.stdout.rstrip("\n") if completed.returncode == 0 else None


def listed_files(root: Path) -> tuple[str, ...]:
    """Return the repository's files: tracked ones and new ones that are not git-ignored.

    Args:
        root: the repository root.

    Returns:
        Repository-relative paths with forward slashes, sorted; files deleted from the working
        tree are left out. Empty when git is unavailable.
    """
    output = run_git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if not output:
        return ()
    paths = {p for p in output.split("\0") if p and (root / p).is_file()}
    return tuple(sorted(paths))
