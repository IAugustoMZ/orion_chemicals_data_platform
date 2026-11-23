"""Adapt stable NumPy seed domains to the pure catalogue draw port."""

import numpy as np

from tssource.domain.errors import TssourceError
from tssource.domain.naming.draws import DrawDomain


class SeededDrawSource:
    """Recreate each independent permutation from the fixture's nonnegative seed."""

    def __init__(self, seed: int) -> None:
        """Keep the root seed for deterministic child streams."""
        if seed < 0:
            raise TssourceError("catalogue seed must be nonnegative")
        self._seed = seed

    def order(self, domain: DrawDomain, size: int) -> tuple[int, ...]:
        """Return a native integer permutation from this domain's child seed."""
        child = np.random.SeedSequence(self._seed, spawn_key=(domain.value,))
        return tuple(int(index) for index in np.random.default_rng(child).permutation(size))
