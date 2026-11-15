"""Timestamp representations that retain the exact source-side value."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from tssource.domain.time.resolution import LocalResolution

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)


class TimestampForm(StrEnum):
    """The six declared source timestamp forms."""

    ISO_OFFSET = "iso-offset"
    ISO_LOCAL = "iso-local"
    EPOCH_SECONDS = "epoch-seconds"
    EPOCH_MILLISECONDS = "epoch-milliseconds"
    LOCAL_TEXT = "local-text"
    FILETIME_TICKS = "filetime-ticks"


@dataclass(frozen=True)
class DecodedTimestamp:
    """A decoded source value with its original representation and explicit resolution."""

    original: str | int | float
    form: TimestampForm
    known_zone_or_offset: str | None
    resolution: LocalResolution


def decode_instant(value: str | int | float, form: TimestampForm) -> datetime:
    """Decode an offset-bearing timestamp form into one UTC instant.

    Raises:
        ValueError: the input is local-only or has no usable offset.
    """
    if form is TimestampForm.ISO_OFFSET:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("ISO offset form requires an offset")
        return parsed.astimezone(UTC)
    if form is TimestampForm.EPOCH_SECONDS:
        return datetime.fromtimestamp(float(value), tz=UTC)
    if form is TimestampForm.EPOCH_MILLISECONDS:
        return datetime.fromtimestamp(float(value) / 1000, tz=UTC)
    if form is TimestampForm.FILETIME_TICKS:
        return _FILETIME_EPOCH + timedelta(microseconds=int(value) / 10)
    raise ValueError("local timestamp requires a site-zone resolver")


def encode_instant(instant: datetime, form: TimestampForm) -> str | int:
    """Encode a UTC instant in an offset-bearing source form without losing the instant."""
    if instant.tzinfo != UTC:
        raise ValueError("instant must be UTC-aware")
    if form is TimestampForm.ISO_OFFSET:
        return instant.isoformat().replace("+00:00", "Z")
    if form is TimestampForm.EPOCH_SECONDS:
        return int(instant.timestamp())
    if form is TimestampForm.EPOCH_MILLISECONDS:
        return int(instant.timestamp() * 1000)
    if form is TimestampForm.FILETIME_TICKS:
        return int((instant - _FILETIME_EPOCH).total_seconds() * 10_000_000)
    raise ValueError("local timestamp requires a site-zone resolver")
