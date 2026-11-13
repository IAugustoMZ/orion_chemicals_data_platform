"""Wall clock for the benchmark: monotonic, so system clock changes cannot bend a measurement."""

from __future__ import annotations

import time


class MonotonicClock:
    """``Clock`` backed by ``time.monotonic``."""

    def now(self) -> float:
        """Seconds on a monotonic scale (only differences mean something)."""
        return time.monotonic()
