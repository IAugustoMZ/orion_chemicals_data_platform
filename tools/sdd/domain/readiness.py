"""Readiness of an artifact: is it complete enough to be approved?

Domain layer. Every artifact starts as a copy of its template in `harness/templates/`. The
template's second-level headings (``## ...``) are the sections the artifact must keep, and every
guidance line the author has to replace is marked ``TODO(sdd)``. An artifact is ready when all
required headings are present and no placeholder remains (a marker quoted in inline code is
prose about the convention, not a placeholder). The template is the single source of
truth: adding a section to a template makes it required everywhere, with no code change.
"""

from __future__ import annotations

import re

PLACEHOLDER = "TODO(sdd)"
"""Marker of text the author must replace before the artifact can be approved."""

_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
_OPTIONAL = "(optional)"
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def required_headings(template_text: str) -> tuple[str, ...]:
    """Return the second-level headings a template makes mandatory.

    Args:
        template_text: the template's Markdown.

    Returns:
        The heading titles in order, excluding those whose title ends with ``(optional)``.
    """
    titles = (m.group("title") for m in _HEADING.finditer(template_text))
    return tuple(t for t in titles if not t.lower().endswith(_OPTIONAL))


def readiness_problems(name: str, text: str | None, headings: tuple[str, ...]) -> tuple[str, ...]:
    """List why an artifact cannot be approved yet.

    Args:
        name: artifact file name, used in the messages.
        text: the artifact's content, or None when the file does not exist.
        headings: the required heading titles (from `required_headings`).

    Returns:
        One message per problem; empty when the artifact is ready.
    """
    if text is None:
        return (f"{name}: file is missing",)
    present = {m.group("title") for m in _HEADING.finditer(text)}
    problems = [f"{name}: missing section '## {h}'" for h in headings if h not in present]
    for number, line in enumerate(text.splitlines(), start=1):
        # A marker inside `backticks` is the document *talking about* the convention.
        if PLACEHOLDER in _INLINE_CODE.sub("", line):
            problems.append(f"{name}:{number}: unresolved {PLACEHOLDER}")
    return tuple(problems)
