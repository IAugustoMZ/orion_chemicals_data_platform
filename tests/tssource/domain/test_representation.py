"""Acceptance tests for source timestamp forms."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tssource.domain.time.representation import TimestampForm, decode_instant, encode_instant
from tssource.domain.time.resolution import ResolutionStatus
from tssource.domain.time.site_zone import SITE_ZONES, SiteCode
from tssource.infrastructure.zoneinfo_resolver import ZoneInfoResolver


@pytest.mark.ac("PBI-001-05:AC3")
@pytest.mark.parametrize(
    "form",
    [
        TimestampForm.ISO_OFFSET,
        TimestampForm.EPOCH_SECONDS,
        TimestampForm.EPOCH_MILLISECONDS,
        TimestampForm.FILETIME_TICKS,
    ],
)
def test_utc_forms_round_trip(form: TimestampForm) -> None:
    """Every UTC-bearing form decodes to the same original physical instant."""
    instant = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert decode_instant(encode_instant(instant, form), form) == instant


@pytest.mark.ac("PBI-001-05:AC4")
def test_local_text_keeps_ambiguity() -> None:
    """Local text remains unresolved when its declared site repeats a wall-clock hour."""
    resolution = ZoneInfoResolver().resolve(
        SITE_ZONES[SiteCode.US_GULF_COAST], datetime(2024, 11, 3, 1, 30)
    )
    assert resolution.status is ResolutionStatus.AMBIGUOUS
