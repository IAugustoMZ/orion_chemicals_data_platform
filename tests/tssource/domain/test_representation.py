"""Acceptance tests for source timestamp forms."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tssource.domain.time.representation import (
    TimestampForm,
    decode_direct,
    decode_instant,
    encode_instant,
)
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


@pytest.mark.ac("PBI-001-24:AC1")
@pytest.mark.parametrize(
    ("value", "form", "instant", "reference"),
    [
        (
            "2024-01-02T03:04:05.123457+05:30",
            TimestampForm.ISO_OFFSET,
            datetime(2024, 1, 1, 21, 34, 5, 123457, tzinfo=UTC),
            "+05:30",
        ),
        ("-1", TimestampForm.EPOCH_SECONDS, datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC), "UTC"),
        (1.0, TimestampForm.EPOCH_SECONDS, datetime(1970, 1, 1, 0, 0, 1, tzinfo=UTC), "UTC"),
        (
            -1,
            TimestampForm.EPOCH_MILLISECONDS,
            datetime(1969, 12, 31, 23, 59, 59, 999000, tzinfo=UTC),
            "UTC",
        ),
        (
            1,
            TimestampForm.EPOCH_MILLISECONDS,
            datetime(1970, 1, 1, 0, 0, 0, 1000, tzinfo=UTC),
            "UTC",
        ),
        (
            1234570,
            TimestampForm.FILETIME_TICKS,
            datetime(1601, 1, 1, 0, 0, 0, 123457, tzinfo=UTC),
            "UTC",
        ),
    ],
)
def test_direct_metadata_and_exact_round_trip(
    value: str | int | float, form: TimestampForm, instant: datetime, reference: str
) -> None:
    """Direct forms preserve raw metadata and recover representable instants exactly."""
    decoded = decode_direct(value, form)
    assert decoded.original == value
    assert type(decoded.original) is type(value)
    assert decoded.form is form
    assert decoded.known_zone_or_offset == reference
    assert decoded.resolution.status is ResolutionStatus.OK
    assert decoded.resolution.candidates == (instant,)
    assert decode_instant(encode_instant(instant, form), form) == instant


@pytest.mark.ac("PBI-001-24:AC2")
@pytest.mark.parametrize(
    ("instant", "form"),
    [
        (datetime(1969, 12, 31, 23, 59, 59, 999999, tzinfo=UTC), TimestampForm.EPOCH_SECONDS),
        (datetime(1970, 1, 1, 0, 0, 0, 1001, tzinfo=UTC), TimestampForm.EPOCH_MILLISECONDS),
        (datetime(1600, 12, 31, 23, 59, 59, tzinfo=UTC), TimestampForm.FILETIME_TICKS),
    ],
)
def test_direct_encode_rejects_unrepresentable_values(
    instant: datetime, form: TimestampForm
) -> None:
    """An inexact or out-of-range encode raises ValueError."""
    with pytest.raises(ValueError, match="precision|before the FILETIME epoch"):
        encode_instant(instant, form)


@pytest.mark.ac("PBI-001-24:AC2")
def test_filetime_does_not_round_to_microseconds() -> None:
    """Ticks between microseconds cannot be decoded as a datetime."""
    with pytest.raises(
        ValueError, match="FILETIME value cannot be represented at microsecond precision"
    ):
        decode_instant(1234571, TimestampForm.FILETIME_TICKS)


def test_iso_offset_does_not_truncate_fractional_precision() -> None:
    """An ISO offset input with excess significant digits cannot be decoded exactly."""
    with pytest.raises(ValueError, match="precision"):
        decode_instant("2024-01-02T03:04:05.1234567Z", TimestampForm.ISO_OFFSET)
    with pytest.raises(ValueError, match="precision"):
        decode_instant("2024-01-02T03:04:05+00:00:00.1234567", TimestampForm.ISO_OFFSET)


def test_epoch_decoding_preserves_previously_supported_exact_fractions() -> None:
    """Signed fractional source units remain usable down to datetime precision."""
    instant = datetime(1969, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    assert decode_instant("-0.000001", TimestampForm.EPOCH_SECONDS) == instant
    assert decode_instant(-0.001, TimestampForm.EPOCH_MILLISECONDS) == instant
    with pytest.raises(ValueError, match="precision"):
        decode_instant("-0.0000001", TimestampForm.EPOCH_SECONDS)


@pytest.mark.ac("PBI-001-25:AC1")
@pytest.mark.parametrize(
    "value",
    [
        "2024-01-02T00:00:00+00:60",
        "2024-01-02T00:00:00+00:00:60",
        "2024-01-02T00:00:00+24:00",
        "2024-01-02T00:00:00+00:00.5",
        "2024-01-02T00:00:00+0000.5",
        "2024-01-02T00:00:00-00.5",
        "2024-01-02T00.5+00:00",
        "2024-01-02T00:30.5+00:00",
    ],
)
def test_iso_decoding_rejects_overflow_and_abbreviated_fractions(value: str) -> None:
    """Overflow and shortened fractions cannot be silently reinterpreted."""
    with pytest.raises(ValueError, match="invalid ISO offset timestamp"):
        decode_instant(value, TimestampForm.ISO_OFFSET)


@pytest.mark.ac("PBI-001-25:AC2")
@pytest.mark.parametrize(
    ("suffix", "offset", "instant"),
    [
        ("Z", "+00:00", datetime(2024, 1, 2, tzinfo=UTC)),
        ("+05:30", "+05:30", datetime(2024, 1, 1, 18, 30, tzinfo=UTC)),
        ("+0530", "+05:30", datetime(2024, 1, 1, 18, 30, tzinfo=UTC)),
        ("+00:00:00.5", "+00:00:00.500000", datetime(2024, 1, 1, 23, 59, 59, 500000, tzinfo=UTC)),
        ("-00:00:00.5", "-00:00:00.500000", datetime(2024, 1, 2, 0, 0, 0, 500000, tzinfo=UTC)),
    ],
)
def test_iso_decoding_preserves_supported_offsets(
    suffix: str, offset: str, instant: datetime
) -> None:
    """Normalize each supported offset without changing its contribution to UTC."""
    raw = f"2024-01-02T00:00:00{suffix}"
    decoded = decode_direct(raw, TimestampForm.ISO_OFFSET)
    assert decoded.original == raw
    assert decoded.known_zone_or_offset == offset
    assert decoded.resolution.candidates == (instant,)


@pytest.mark.parametrize(
    "value",
    ["20240102T000000+000000,0000000", "2024-W01-2T00:00Z", "2024W012T00+00"],
)
def test_iso_decoding_preserves_existing_exact_spellings(value: str) -> None:
    """Compact dates, week dates and whole abbreviated values still decode exactly."""
    assert decode_instant(value, TimestampForm.ISO_OFFSET) == datetime(2024, 1, 2, tzinfo=UTC)
