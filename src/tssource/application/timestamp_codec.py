"""Convert source timestamps without guessing site context or a repeated-hour fold."""

from __future__ import annotations

from datetime import datetime

from tssource.application.time_table import ZoneResolver
from tssource.domain.time.representation import (
    DecodedTimestamp,
    TimestampForm,
    decode_direct,
    encode_instant,
    format_offset,
    parse_local,
    render_local,
)
from tssource.domain.time.site_zone import SITE_ZONES, SiteZone


class TimestampCodec:
    """Coordinate exact format conversion and declared-site resolution."""

    def __init__(self, resolver: ZoneResolver) -> None:
        """Keep zone lookup behind the same port used by the time table."""
        self._resolver = resolver

    def encode(
        self, instant: datetime, form: TimestampForm, site: SiteZone | None = None
    ) -> str | int:
        """Encode a UTC instant, requiring a declared site for wall-clock forms."""
        if not form.is_local:
            return encode_instant(instant, form)
        local = self._resolver.to_local(self._declared_site(site), instant)
        return render_local(local, form)

    def decode(
        self, value: str | int | float, form: TimestampForm, site: SiteZone | None = None
    ) -> DecodedTimestamp:
        """Retain source metadata and all valid UTC interpretations of the input."""
        if not form.is_local:
            return decode_direct(value, form)
        declared = self._declared_site(site)
        resolution = self._resolver.resolve(declared, parse_local(value, form))
        reference = (
            declared.zone_name
            if declared.fixed_offset is None
            else format_offset(declared.fixed_offset)
        )
        return DecodedTimestamp(value, form, reference, resolution)

    @staticmethod
    def _declared_site(site: SiteZone | None) -> SiteZone:
        """Reject missing or inconsistent site declarations for local forms."""
        if site is None or SITE_ZONES.get(site.code) != site:
            raise ValueError("local timestamp requires a declared site")
        return site
