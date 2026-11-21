"""Acceptance tests for site-aware timestamp conversions through bootstrap."""

from datetime import UTC, datetime

import pytest

from tssource.bootstrap import build_timestamp_codec
from tssource.domain.time.representation import TimestampForm
from tssource.domain.time.resolution import ResolutionStatus
from tssource.domain.time.site_zone import SITE_ZONES, SiteCode


@pytest.mark.ac("PBI-001-24:AC3")
@pytest.mark.parametrize(
    ("form", "ordinary", "repeated", "skipped"),
    [
        (
            TimestampForm.ISO_LOCAL,
            "2024-01-02T01:30:00",
            "2024-11-03T01:30:00",
            "2024-03-10T02:30:00",
        ),
        (
            TimestampForm.LOCAL_TEXT,
            "01/02/2024 01:30:00",
            "11/03/2024 01:30:00",
            "03/10/2024 02:30:00",
        ),
    ],
)
def test_local_codec_preserves_declared_site_resolution(
    form: TimestampForm, ordinary: str, repeated: str, skipped: str
) -> None:
    """Both forms retain ordinary, repeated, and skipped wall readings."""
    codec = build_timestamp_codec()
    site = SITE_ZONES[SiteCode.US_GULF_COAST]
    ordinary_instant = datetime(2024, 1, 2, 7, 30, tzinfo=UTC)
    candidates = (
        datetime(2024, 11, 3, 6, 30, tzinfo=UTC),
        datetime(2024, 11, 3, 7, 30, tzinfo=UTC),
    )
    assert codec.encode(ordinary_instant, form, site) == ordinary
    assert codec.decode(ordinary, form, site).resolution.candidates == (ordinary_instant,)
    assert codec.decode(ordinary, form, site).resolution.status is ResolutionStatus.OK
    for candidate in candidates:
        assert codec.encode(candidate, form, site) == repeated
    decoded = codec.decode(repeated, form, site)
    assert decoded.original == repeated
    assert decoded.form is form
    assert decoded.known_zone_or_offset == "America/Chicago"
    assert decoded.resolution.status is ResolutionStatus.AMBIGUOUS
    assert decoded.resolution.candidates == candidates
    gap = codec.decode(skipped, form, site)
    assert gap.original == skipped
    assert gap.resolution.status is ResolutionStatus.GAP
    assert gap.resolution.candidates == (datetime(2024, 3, 10, 8, tzinfo=UTC),)
    with pytest.raises(ValueError, match="site"):
        codec.encode(ordinary_instant, form)
    with pytest.raises(ValueError, match="site"):
        codec.decode(ordinary, form)


@pytest.mark.ac("PBI-001-24:AC2")
def test_local_text_rejects_subsecond_precision() -> None:
    """Encoding local text never discards original subsecond precision."""
    codec = build_timestamp_codec()
    site = SITE_ZONES[SiteCode.CHINA]
    instant = datetime(2024, 1, 2, 7, 30, 0, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="precision"):
        codec.encode(instant, TimestampForm.LOCAL_TEXT, site)
    encoded = codec.encode(instant, TimestampForm.ISO_LOCAL, site)
    assert codec.decode(encoded, TimestampForm.ISO_LOCAL, site).resolution.candidates == (instant,)


@pytest.mark.ac("PBI-001-24:AC5")
@pytest.mark.parametrize("form", [TimestampForm.ISO_LOCAL, TimestampForm.LOCAL_TEXT])
@pytest.mark.parametrize(
    ("site_code", "year", "month", "day", "hour", "minute", "reference"),
    [
        (SiteCode.CHINA, 1991, 4, 14, 4, 0, "+08:00"),
        (SiteCode.INDIA, 1942, 9, 1, 6, 30, "+05:30"),
        (SiteCode.CHINA, 2024, 1, 2, 4, 0, "+08:00"),
        (SiteCode.INDIA, 2024, 1, 2, 6, 30, "+05:30"),
    ],
)
def test_fixed_site_offsets_apply_even_on_historical_dates(
    form: TimestampForm,
    site_code: SiteCode,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    reference: str,
) -> None:
    """The codec and resolver use the declared offset even when IANA rules differed."""
    codec = build_timestamp_codec()
    site = SITE_ZONES[site_code]
    raw = (
        f"{year:04}-{month:02}-{day:02}T12:00:00"
        if form is TimestampForm.ISO_LOCAL
        else f"{month:02}/{day:02}/{year:04} 12:00:00"
    )
    instant = datetime(year, month, day, hour, minute, tzinfo=UTC)
    decoded = codec.decode(raw, form, site)
    assert decoded.original == raw
    assert decoded.known_zone_or_offset == reference
    assert decoded.resolution.status is ResolutionStatus.OK
    assert decoded.resolution.candidates == (instant,)
    assert codec.encode(instant, form, site) == raw


@pytest.mark.ac("PBI-001-24:AC1")
def test_direct_codec_does_not_require_a_site() -> None:
    """The public codec returns direct metadata without a site or a zone lookup."""
    codec = build_timestamp_codec()
    instant = datetime(2024, 1, 1, 12, 30, 0, 123457, tzinfo=UTC)
    raw = "2024-01-01T18:00:00.123457+05:30"
    decoded = codec.decode(raw, TimestampForm.ISO_OFFSET)
    assert decoded.original == raw
    assert decoded.known_zone_or_offset == "+05:30"
    assert decoded.resolution.requested_local == datetime(2024, 1, 1, 18, 0, 0, 123457)
    assert decoded.resolution.candidates == (instant,)
    assert codec.encode(instant, TimestampForm.ISO_OFFSET) == "2024-01-01T12:30:00.123457Z"
