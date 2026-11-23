"""Provide independent fixture permutations to the catalogue domain."""

from enum import IntEnum
from typing import Protocol


class DrawDomain(IntEnum):
    """Assign stable seed domains to unrelated decisions."""

    VARIANTS = 1
    DESCRIPTORS = 2
    UNITS = 3
    HOLDOUT = 4


class DrawSource(Protocol):
    """Provide a deterministic permutation of indices for a named decision."""

    def order(self, domain: DrawDomain, size: int) -> tuple[int, ...]:
        """Return every index in range(size) once in seeded order."""
        ...
