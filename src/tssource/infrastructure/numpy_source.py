"""Throwaway event source for the spike: seeded random walks for every tag, in numpy blocks.

Infrastructure layer. One ``Generator.standard_normal`` call makes a whole block (ticks x tags)
and a cumulative sum continues each walk, so generation is vectorised. Signal realism is out of
scope (card 02 only asks whether Python can move the bytes); the output is deterministic per seed.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from tssource.domain.benchmark import Block

TAGS = 2050
"""Tags in the plant catalogue (RT28): one value per tag per scan tick."""
TICKS_PER_BLOCK = 25
"""Scan ticks per block: 25 x 2,050 = 51,250 events, a few MB, a good unit for the queue."""
_TICK_MS = 1000
_EPOCH_MS = 1_767_225_600_000  # 2026-01-01T00:00:00Z, fixed so runs are comparable


class Columns(NamedTuple):
    """The payload of one block: three equal-length columns, one row per event."""

    timestamps_ms: NDArray[np.int64]
    tag_ids: NDArray[np.int32]
    values: NDArray[np.float64]


class NumpyBlockSource:
    """``EventSource`` made of seeded random walks."""

    def __init__(self, seed: int) -> None:
        """Seed the generator; the same seed always gives the same blocks."""
        self._rng = np.random.default_rng(seed)
        self._level = np.zeros(TAGS, dtype=np.float64)
        self._tick = 0
        self._tag_ids = np.tile(np.arange(TAGS, dtype=np.int32), TICKS_PER_BLOCK)

    def next_block(self) -> Block:
        """Advance every walk by ``TICKS_PER_BLOCK`` ticks and return the events."""
        steps = self._rng.standard_normal((TICKS_PER_BLOCK, TAGS))
        walk = self._level + np.cumsum(steps, axis=0)
        self._level = walk[-1]
        ticks = np.arange(self._tick, self._tick + TICKS_PER_BLOCK, dtype=np.int64)
        self._tick += TICKS_PER_BLOCK
        timestamps = np.repeat(_EPOCH_MS + ticks * _TICK_MS, TAGS)
        columns = Columns(timestamps, self._tag_ids, walk.ravel())
        return Block(count=int(columns.values.size), payload=columns)
