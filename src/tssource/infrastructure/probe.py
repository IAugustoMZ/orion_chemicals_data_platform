"""Process cost of a run, from the standard library only (no new dependency).

Infrastructure layer. CPU seconds come from ``time.process_time`` (all threads). Peak memory comes
from ``resource.getrusage``, which exists on Linux (the container, where the numbers that count
are taken) and not on Windows, where it reports 0.0 instead of guessing.
"""

from __future__ import annotations

import sys
import time


class ProcessResourceProbe:
    """``ResourceProbe`` for the running process."""

    def cpu_seconds(self) -> float:
        """CPU seconds (user + system, every thread) used by this process so far."""
        return time.process_time()

    def peak_memory_mb(self) -> float:
        """Peak resident set size in MB; 0.0 where the platform cannot tell (Windows)."""
        if sys.platform == "win32":
            return 0.0
        import resource  # noqa: PLC0415 - only exists off Windows

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux reports KiB, macOS reports bytes.
        return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024
