"""Timestamp representations that retain the exact source-side value."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import cast

from tssource.domain.time.resolution import LocalResolution, ResolutionStatus

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MICROSECONDS_PER_SECOND = 1_000_000
_ISO_LOCAL = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?")
_LOCAL_TEXT = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}")
_ISO_OFFSET = re.compile(
    r"""
    # The calendar or week date can use extended or compact notation.
    [0-9]{4} (?: -[0-9]{2}-[0-9]{2} | [0-9]{4} | -W[0-9]{2}(?:-[0-9])? | W[0-9]{2}[0-9]? )
    .
    # A wall-clock fraction requires an explicit seconds field.
    [0-9]{2} (?: (?P<wall_sep>:?) [0-9]{2}
        (?: (?P=wall_sep) [0-9]{2} (?:[.,](?P<wall_fraction>[0-9]+))? )?
    )?
    # Check offset field ranges before datetime can normalize them.
    (?: Z | (?P<sign>[+-]) (?:[01][0-9]|2[0-3]) (?: (?P<offset_sep>:?) [0-5][0-9]
        (?: (?P=offset_sep) [0-5][0-9] (?:[.,](?P<offset_fraction>[0-9]+))? )?
    )? )
    """,
    re.VERBOSE | re.DOTALL,
)


class TimestampForm(StrEnum):
    """The six declared source timestamp forms."""

    ISO_OFFSET = "iso-offset"
    ISO_LOCAL = "iso-local"
    EPOCH_SECONDS = "epoch-seconds"
    EPOCH_MILLISECONDS = "epoch-milliseconds"
    LOCAL_TEXT = "local-text"
    FILETIME_TICKS = "filetime-ticks"

    @property
    def is_local(self) -> bool:
        """Identify forms whose source text needs a separate site declaration."""
        return self in (TimestampForm.ISO_LOCAL, TimestampForm.LOCAL_TEXT)


@dataclass(frozen=True)
class DecodedTimestamp:
    """A decoded source value with its original representation and explicit resolution."""

    original: str | int | float
    form: TimestampForm
    known_zone_or_offset: str | None
    resolution: LocalResolution


def decode_instant(value: str | int | float, form: TimestampForm) -> datetime:
    """Decode a directly resolved source form into a single UTC instant."""
    return decode_direct(value, form).resolution.candidates[0]


def decode_direct(value: str | int | float, form: TimestampForm) -> DecodedTimestamp:
    """Decode without rounding and preserve the original value and source reference."""
    if form.is_local:
        raise ValueError("local timestamp requires a site-zone resolver")
    try:
        if form is TimestampForm.ISO_OFFSET:
            parsed = _parse_iso_offset(str(value))
            offset = parsed.utcoffset()
            if offset is None:
                raise ValueError("ISO offset form requires an offset")
            instant = parsed.astimezone(UTC)
            reference = format_offset(offset)
        else:
            instant = _decode_numeric(value, form)
            parsed = instant
            offset = timedelta()
            reference = "UTC"
    except OverflowError as error:
        raise ValueError("timestamp is outside the supported UTC range") from error
    resolution = LocalResolution(
        parsed.replace(tzinfo=None), ResolutionStatus.OK, (instant,), (offset,)
    )
    return DecodedTimestamp(value, form, reference, resolution)


def _parse_iso_offset(value: str) -> datetime:
    """Validate ISO components before Python can normalize them or truncate precision."""
    match = _ISO_OFFSET.fullmatch(value)
    if match is None:
        raise ValueError("invalid ISO offset timestamp")
    wall_fraction = match["wall_fraction"] or ""
    offset_fraction = match["offset_fraction"] or ""
    if wall_fraction[6:].strip("0") or offset_fraction[6:].strip("0"):
        raise ValueError("ISO offset input exceeds datetime precision")
    parsed = datetime.fromisoformat(value)
    if offset_fraction and parsed.utcoffset() == timedelta():
        # fromisoformat can discard a fractional offset whose whole seconds are zero.
        microseconds = int(offset_fraction[:6].ljust(6, "0"))
        if match["sign"] == "-":
            microseconds = -microseconds
        return parsed.replace(tzinfo=timezone(timedelta(microseconds=microseconds)))
    return parsed


def _decode_numeric(value: str | int | float, form: TimestampForm) -> datetime:
    """Convert exact numeric source units to microseconds before constructing a datetime."""
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("timestamp requires a numeric value") from error
    if not number.is_finite():
        raise ValueError("timestamp requires a finite numeric value")
    if number and number.adjusted() > 19:
        raise ValueError("timestamp is outside the supported UTC range")
    if form is TimestampForm.FILETIME_TICKS:
        return _decode_filetime(number)
    places = 6 if form is TimestampForm.EPOCH_SECONDS else 3
    return _UNIX_EPOCH + timedelta(microseconds=_scaled_epoch_units(number, places))


def _decode_filetime(number: Decimal) -> datetime:
    """Require integral FILETIME ticks that fit exactly in datetime microseconds."""
    if number < 0 or number != number.to_integral_value():
        raise ValueError("FILETIME requires non-negative integral ticks")
    microseconds, remainder = divmod(int(number), 10)
    if remainder:
        raise ValueError("FILETIME value cannot be represented at microsecond precision")
    return _FILETIME_EPOCH + timedelta(microseconds=microseconds)


def _scaled_epoch_units(number: Decimal, places: int) -> int:
    """Shift a finite decimal exponent without rounding or using the Decimal context."""
    if not number:
        return 0
    if number.adjusted() < -places:
        raise ValueError("epoch value exceeds datetime precision")
    sign, digits, exponent = number.as_tuple()
    scaled = Decimal((sign, digits, cast(int, exponent) + places))
    if scaled != scaled.to_integral_value():
        raise ValueError("epoch value exceeds datetime precision")
    return int(scaled)


def encode_instant(instant: datetime, form: TimestampForm) -> str | int:
    """Encode a UTC instant in a direct form, rejecting precision loss and overflow."""
    if instant.tzinfo != UTC:
        raise ValueError("instant must be UTC-aware")
    if form is TimestampForm.ISO_OFFSET:
        return instant.isoformat().replace("+00:00", "Z")
    if form is TimestampForm.FILETIME_TICKS:
        if instant < _FILETIME_EPOCH:
            raise ValueError("instant is before the FILETIME epoch")
        return _total_microseconds(instant - _FILETIME_EPOCH) * 10
    if form.is_local:
        raise ValueError("local timestamp requires a site-zone resolver")
    unit = _MICROSECONDS_PER_SECOND if form is TimestampForm.EPOCH_SECONDS else 1000
    units, remainder = divmod(_total_microseconds(instant - _UNIX_EPOCH), unit)
    if remainder:
        raise ValueError(f"instant exceeds {form.value} precision")
    return units


def _total_microseconds(delta: timedelta) -> int:
    """Count signed UTC microseconds without passing through floating point."""
    return (delta.days * 86_400 + delta.seconds) * _MICROSECONDS_PER_SECOND + delta.microseconds


def parse_local(value: str | int | float, form: TimestampForm) -> datetime:
    """Parse local fixture text according to its declared shape and precision."""
    if isinstance(value, str):
        if form is TimestampForm.ISO_LOCAL and _ISO_LOCAL.fullmatch(value):
            return datetime.fromisoformat(value)
        if form is TimestampForm.LOCAL_TEXT and _LOCAL_TEXT.fullmatch(value):
            return datetime.strptime(value, "%m/%d/%Y %H:%M:%S")
    raise ValueError(f"invalid {form.value} timestamp")


def render_local(local: datetime, form: TimestampForm) -> str:
    """Render a projected wall time at the chosen form's supported precision."""
    if form is TimestampForm.ISO_LOCAL:
        return local.isoformat()
    if local.microsecond:
        raise ValueError("instant exceeds local-text precision")
    return f"{local.month:02}/{local.day:02}/{local.year:04} {local:%H:%M:%S}"


def format_offset(offset: timedelta) -> str:
    """Format a signed UTC offset, including seconds and fractions when present."""
    return datetime(2000, 1, 1, tzinfo=timezone(offset)).isoformat()[19:]
