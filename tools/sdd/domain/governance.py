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
    ".github/",
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


_ITEM_BRANCH = re.compile(r"^feat/(?P<id>\d{3})-(?P<number>\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_SLUG = 40


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


def item_from_branch(branch: str) -> tuple[str, str] | None:
    """Extract the dossier id and card number from a card branch name.

    Args:
        branch: the current git branch, e.g. ``feat/002-03-item-flow``.

    Returns:
        ``("002", "03")``, or None when the branch is not a card branch.
    """
    match = _ITEM_BRANCH.match(branch)
    return (match.group("id"), match.group("number")) if match else None


def item_branch_name(dossier_id: str, number: str, title: str) -> str:
    """Build the branch name of a card from its heading.

    Args:
        dossier_id: three-digit dossier id.
        number: the card number, ``"03"``.
        title: the card heading, e.g. ``PBI-002-03 · Item flow: branch and guard``.

    Returns:
        ``feat/<id>-<nn>-<slug>``; the slug is the lower-cased title without the PBI id,
        cut at a word boundary within 40 characters (``card`` when nothing is left).
    """
    text = title.split("·", 1)[1] if "·" in title else title
    words = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = words[:_MAX_SLUG].rsplit("-", 1)[0] if len(words) > _MAX_SLUG else words
    return f"feat/{dossier_id}-{number}-{slug or 'card'}"
