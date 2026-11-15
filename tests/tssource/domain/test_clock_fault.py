"""Acceptance tests for deterministic source-clock faults."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from tssource.domain.time.clock_fault import ClockFault


@pytest.mark.ac("PBI-001-05:AC5")
def test_clock_fault_applies_offset_and_accumulated_drift() -> None:
    """A fault shifts written occurrence by the configured offset plus elapsed whole-day drift."""
    start = datetime(2024, 1, 1, tzinfo=UTC)
    fault = ClockFault(timedelta(minutes=5), timedelta(minutes=1), start)
    assert fault.apply(start + timedelta(days=2)) == start + timedelta(days=2, minutes=7)
