"""Adapter of the `Clock` port: the system clock, in UTC.

Infrastructure layer. Every timestamp the harness writes is timezone-aware UTC (the same rule
the platform follows for data, RT12), seconds precision, so files stay readable and stable.
"""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Return the current UTC time."""

    def now(self) -> datetime:
        """Return now, timezone-aware, truncated to whole seconds."""
        return datetime.now(UTC).replace(microsecond=0)
