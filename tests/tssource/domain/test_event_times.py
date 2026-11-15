"""Acceptance tests for RT07's three timestamp invariant."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tssource.domain.time.event_times import EventTimes


@pytest.mark.ac("PBI-001-05:AC5")
def test_event_times_remain_separate_utc_values() -> None:
    """Occurrence, update, and reception are stored separately rather than collapsed."""
    times = EventTimes(
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    )
    assert len({times.occurrence, times.source_update, times.reception}) == 3
