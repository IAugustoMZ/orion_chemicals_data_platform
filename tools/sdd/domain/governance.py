"""Which files are *governed*, and which branch a change belongs to.

Domain layer. A governed file is one whose change alters the system's behaviour or its rules:
code, tests, container and dependency definitions, the harness and the agent configuration.
The Constitution (article III) says governed files change only on a spec branch
(``spec/<id>-<slug>``) whose specification was approved (gate G4). Documentation and dossiers
are not governed: we may write and discuss them at any time.
"""

from __future__ import annotations

import re

GOVERNED_DIRECTORIES: tuple[str, ...] = (
    "tools/",
    "src/",
    "tests/",
    "docker/",
    "harness/",
    ".agents/",
    ".claude/",
)
"""Directory prefixes whose files are governed (repository-relative, forward slashes)."""

GOVERNED_FILES: tuple[str, ...] = (
    "pyproject.toml",
    "poetry.lock",
    "compose.yaml",
    ".pre-commit-config.yaml",
    "mkdocs.yml",
    "AGENTS.md",
)
"""Single files at the repository root that are governed."""

_SPEC_BRANCH = re.compile(r"^spec/(?P<id>\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_governed(path: str) -> bool:
    """Tell whether a change to `path` needs an approved specification.

    Args:
        path: repository-relative path; backslashes (Windows) are accepted.

    Returns:
        True for files under a governed directory or in the governed root-file list.
    """
    normalised = path.replace("\\", "/").removeprefix("./")
    return normalised in GOVERNED_FILES or normalised.startswith(GOVERNED_DIRECTORIES)


def spec_id_from_branch(branch: str) -> str | None:
    """Extract the dossier id from a spec branch name.

    Args:
        branch: the current git branch, e.g. ``spec/001-source-contracts``.

    Returns:
        The id (``"001"``), or None when the branch is not a spec branch.
    """
    match = _SPEC_BRANCH.match(branch)
    return match.group("id") if match else None
