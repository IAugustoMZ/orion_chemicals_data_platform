"""Backlog cards as sections of `backlog.md`: split, fingerprint, and read their criteria.

Domain layer, pure functions on text. A card is the section that starts at a heading
``### PBI-<dossier>-<nn> · title`` and ends at the next heading of level 1 to 3. Approving one
card binds the approval to the digest of its own section, so editing card 03 makes only card
03's approval stale (PBI-002-02 AC2).
"""

from __future__ import annotations

import re

from sdd.domain.digest import digest_texts

_CARD_HEADING = re.compile(r"^### PBI-\d{3}-(?P<number>\d{2})\b")
_ANY_HEADING = re.compile(r"^#{1,3} ")
_CRITERION = re.compile(r"^\s*[-*]\s+(?P<ac>AC\d+):", re.MULTILINE)


def card_sections(backlog: str) -> dict[str, str]:
    """Split a backlog into its cards.

    Args:
        backlog: the text of `backlog.md`.

    Returns:
        Card number (``"01"``) to the card's section text, heading included, in file order.
    """
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in backlog.splitlines():
        match = _CARD_HEADING.match(line)
        if match:
            current = sections.setdefault(match.group("number"), [])
        elif _ANY_HEADING.match(line):
            current = None
        if current is not None:
            current.append(line)
    return {number: "\n".join(lines) for number, lines in sections.items()}


def card_digest(section: str) -> str:
    """Return the digest an approval of one card is bound to.

    Args:
        section: the card's section text from `card_sections`.
    """
    return digest_texts((("card", section),))


def acceptance_criteria(section: str) -> tuple[str, ...]:
    """Return the acceptance criteria ids of a card, in order.

    Args:
        section: the card's section text.

    Returns:
        ``("AC1", "AC2", ...)``; empty when the card lists none.
    """
    return tuple(match.group("ac") for match in _CRITERION.finditer(section))


def backlog_without_card_bodies(backlog: str) -> str:
    """Return the backlog as gate G2 judges it: structure plus the first card in full.

    The other cards keep only their heading, because each one is approved on its own later.

    Args:
        backlog: the text of `backlog.md`.

    Returns:
        The text with the body of every card but the first removed.
    """
    kept: list[str] = []
    seen = 0
    inside = False
    for line in backlog.splitlines():
        if _CARD_HEADING.match(line):
            seen += 1
            inside = True
            kept.append(line)
            continue
        if _ANY_HEADING.match(line):
            inside = False
        if not inside or seen == 1:
            kept.append(line)
    return "\n".join(kept)
