"""Explicit outcomes for resolving a local civil time to UTC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class TimeRangeError(ValueError):
    """The source or UTC datetime exceeds the supported calendar range."""


class ResolutionStatus(StrEnum):
    """Whether a local civil value has zero, one, or two physical instants."""

    OK = "ok"
    AMBIGUOUS = "ambiguous"
    GAP = "gap"


@dataclass(frozen=True)
class LocalResolution:
    """Preserve a requested local value and every defensible UTC candidate."""

    requested_local: datetime
    status: ResolutionStatus
    candidates: tuple[datetime, ...]
    offsets: tuple[timedelta, ...]

    def __post_init__(self) -> None:
        """Reject naive or non-UTC candidates so consumers never infer a timezone."""
        if self.requested_local.tzinfo is not None:
            raise ValueError("requested local time must be naive")
        if any(candidate.tzinfo != UTC for candidate in self.candidates):
            raise ValueError("resolution candidates must be UTC-aware")
        if len(self.offsets) != len(self.candidates):
            raise ValueError("every UTC candidate must retain its source offset")
