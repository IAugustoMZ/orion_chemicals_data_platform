"""Use case and port for showing declared-site civil-time resolution."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Protocol

from tssource.domain.time.resolution import LocalResolution
from tssource.domain.time.site_zone import SiteZone


class ZoneResolver(Protocol):
    """Resolve local civil values under the rules of a declared site."""

    def resolve(self, site: SiteZone, local: datetime) -> LocalResolution:
        """Return every UTC interpretation, or a visible daylight-saving gap result."""
        ...

    def to_local(self, site: SiteZone, instant: datetime) -> datetime:
        """Project a UTC instant onto the declared site's wall clock."""
        ...


class ResolveTimeTable:
    """Produce the stable 24-row diagnostic table requested by the CLI."""

    def __init__(self, resolver: ZoneResolver) -> None:
        """Store the civil-time resolver port so zone mechanics stay outside the use case."""
        self._resolver = resolver

    def resolve(self, site: SiteZone, requested_date: date) -> tuple[LocalResolution, ...]:
        """Resolve each top-of-hour local value from 00:00 through 23:00."""
        return tuple(
            self._resolver.resolve(site, datetime.combine(requested_date, time(hour)))
            for hour in range(24)
        )
