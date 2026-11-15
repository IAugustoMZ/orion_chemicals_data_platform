"""Deterministic source-clock faults for later synthetic event generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class ClockFault:
    """Apply a constant offset and optional whole-day drift to a UTC occurrence value."""

    offset: timedelta = timedelta()
    drift_per_day: timedelta = timedelta()
    starts_at: datetime | None = None

    def apply(self, occurrence: datetime) -> datetime:
        """Return the written occurrence value, leaving inactive faults unchanged."""
        _require_utc(occurrence)
        if self.starts_at is None:
            return occurrence + self.offset
        _require_utc(self.starts_at)
        if occurrence < self.starts_at:
            return occurrence
        return occurrence + self.offset + self.drift_per_day * (occurrence - self.starts_at).days


def _require_utc(value: datetime) -> None:
    """Ensure a datetime is an unambiguous UTC instant."""
    if value.tzinfo != UTC:
        raise ValueError("time values must be UTC-aware")
