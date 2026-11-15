"""Acceptance tests for declared-site daylight-saving resolution."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tssource.domain.time.resolution import ResolutionStatus
from tssource.domain.time.site_zone import SITE_ZONES, SiteCode
from tssource.infrastructure.zoneinfo_resolver import ZoneInfoResolver


@pytest.mark.ac("PBI-001-05:AC1")
@pytest.mark.parametrize(
    ("site", "local", "expected"),
    [
        (SiteCode.US_GULF_COAST, datetime(2024, 3, 10, 2), datetime(2024, 3, 10, 8, tzinfo=UTC)),
        (SiteCode.BELGIUM, datetime(2024, 3, 31, 2), datetime(2024, 3, 31, 1, tzinfo=UTC)),
    ],
)
def test_gap_returns_first_valid_instant(
    site: SiteCode, local: datetime, expected: datetime
) -> None:
    """A skipped hour remains visible while resolving to its first physical instant."""
    resolution = ZoneInfoResolver().resolve(SITE_ZONES[site], local)
    assert resolution.status is ResolutionStatus.GAP
    assert resolution.candidates == (expected,)


@pytest.mark.ac("PBI-001-05:AC2")
def test_repeated_time_returns_both_instants() -> None:
    """A repeated Chicago hour produces both UTC interpretations rather than selecting one."""
    resolution = ZoneInfoResolver().resolve(
        SITE_ZONES[SiteCode.US_GULF_COAST], datetime(2024, 11, 3, 1)
    )
    assert resolution.status is ResolutionStatus.AMBIGUOUS
    assert resolution.candidates == (
        datetime(2024, 11, 3, 6, tzinfo=UTC),
        datetime(2024, 11, 3, 7, tzinfo=UTC),
    )
