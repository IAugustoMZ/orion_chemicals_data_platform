"""Helpers that read the structure of a Markdown document (fenced blocks, prose lines).

Application layer, pure functions shared by the documentation rules. They are deliberately
small regular-expression readers, not a full Markdown parser: our documents follow the
conventions of `harness/documentation-standard.md`, and the rules only need fences and lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE = re.compile(r"^(?P<indent>\s*)(?P<marks>`{3,}|~{3,})\s*(?P<info>[\w+-]*)")


@dataclass(frozen=True)
class FencedBlock:
    """A fenced code block.

    Attributes:
        language: the info string after the opening fence ("mermaid", "python", or "").
        start_line: 1-based line number of the opening fence.
        lines: the block's content lines, without the fences.
    """

    language: str
    start_line: int
    lines: tuple[str, ...]


def fenced_blocks(text: str) -> tuple[FencedBlock, ...]:
    """Return every fenced block of a Markdown text, in order.

    Args:
        text: the document.

    Returns:
        The blocks; an unclosed fence runs to the end of the document.
    """
    blocks: list[FencedBlock] = []
    opening: tuple[str, str, int] | None = None
    content: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if opening is None and match:
            opening, content = (match.group("marks"), match.group("info"), number), []
        elif opening is not None and match and match.group("marks").startswith(opening[0]):
            blocks.append(FencedBlock(opening[1].lower(), opening[2], tuple(content)))
            opening = None
        elif opening is not None:
            content.append(line)
    if opening is not None:
        blocks.append(FencedBlock(opening[1].lower(), opening[2], tuple(content)))
    return tuple(blocks)


def prose_lines(text: str) -> tuple[tuple[int, str], ...]:
    """Return the (line number, line) pairs that are outside fenced blocks and inline code.

    Args:
        text: the document.

    Returns:
        The prose lines; inline code spans (`like this`) are blanked out so their content is
        never mistaken for a link.
    """
    inside: str | None = None
    lines: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if match and (inside is None or match.group("marks").startswith(inside)):
            inside = match.group("marks") if inside is None else None
            continue
        if inside is None:
            lines.append((number, re.sub(r"`[^`]*`", "``", line)))
    return tuple(lines)
