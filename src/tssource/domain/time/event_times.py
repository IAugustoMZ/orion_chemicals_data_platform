"""The three distinct timestamps required for a source event."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class EventTimes:
    """Keep occurrence, source update, and reception as separate UTC-aware instants."""

    occurrence: datetime
    source_update: datetime
    reception: datetime

    def __post_init__(self) -> None:
        """Reject naive values because RT07 comparisons require physical instants."""
        if any(value.tzinfo != UTC for value in self._values()):
            raise ValueError("event times must be UTC-aware")

    def _values(self) -> tuple[datetime, datetime, datetime]:
        """Return every retained timestamp for invariant validation."""
        return self.occurrence, self.source_update, self.reception
