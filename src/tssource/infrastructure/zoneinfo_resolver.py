"""Apply declared fixed offsets and IANA civil-time transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

from tssource.domain.time.resolution import LocalResolution, ResolutionStatus, TimeRangeError
from tssource.domain.time.site_zone import SiteZone

_ONE_MICROSECOND = timedelta(microseconds=1)


class ZoneInfoResolver:
    """Resolve both directions under the declared site's time policy."""

    def resolve(self, site: SiteZone, local: datetime) -> LocalResolution:
        """Classify valid, repeated, and skipped local values using UTC round-trips."""
        if local.tzinfo is not None:
            raise ValueError("local time must be naive")
        zone = self._zone(site)
        try:
            if site.fixed_offset is not None:
                instant = local.replace(tzinfo=zone).astimezone(UTC)
                return LocalResolution(
                    local, ResolutionStatus.OK, (instant,), (site.fixed_offset,)
                )
            return self._resolve_civil(zone, local)
        except OverflowError as error:
            raise TimeRangeError("local time is outside the supported UTC range") from error

    def to_local(self, site: SiteZone, instant: datetime) -> datetime:
        """Project a UTC instant into the site's naive wall-clock representation."""
        if instant.tzinfo != UTC:
            raise ValueError("instant must be UTC-aware")
        try:
            return instant.astimezone(self._zone(site)).replace(tzinfo=None)
        except OverflowError as error:
            raise TimeRangeError("instant is outside the supported local time range") from error

    @staticmethod
    def _zone(site: SiteZone) -> tzinfo:
        """Use fixed-offset arithmetic without loading an IANA zone for fixed sites."""
        if site.fixed_offset is not None:
            return timezone(site.fixed_offset)
        return ZoneInfo(site.zone_name)

    def _resolve_civil(self, zone: tzinfo, local: datetime) -> LocalResolution:
        """Check both folds and search for the boundary only if neither round-trips."""
        probes = tuple(
            sorted({local.replace(tzinfo=zone, fold=fold).astimezone(UTC) for fold in (0, 1)})
        )
        candidates = tuple(
            probe for probe in probes if probe.astimezone(zone).replace(tzinfo=None) == local
        )
        if not candidates:
            boundary = self._gap_boundary(zone, probes[0], probes[-1])
            return LocalResolution(
                local, ResolutionStatus.GAP, (boundary,), (self._offset(zone, boundary),)
            )
        status = ResolutionStatus.OK if len(candidates) == 1 else ResolutionStatus.AMBIGUOUS
        return LocalResolution(
            local, status, candidates, tuple(self._offset(zone, value) for value in candidates)
        )

    def _gap_boundary(self, zone: tzinfo, before: datetime, after: datetime) -> datetime:
        """Bisect the two UTC folds to find the first microsecond at the new offset."""
        old_offset = self._offset(zone, before)
        new_offset = self._offset(zone, after)
        if before >= after or new_offset <= old_offset:
            raise ValueError("UTC folds did not bracket a forward offset transition")
        while after - before > _ONE_MICROSECOND:
            midpoint = before + (after - before) // 2
            if self._offset(zone, midpoint) == old_offset:
                before = midpoint
            else:
                after = midpoint
        return after

    @staticmethod
    def _offset(zone: tzinfo, instant: datetime) -> timedelta:
        """Read the site's UTC offset at the given physical instant."""
        offset = instant.astimezone(zone).utcoffset()
        if offset is None:
            raise ValueError("declared zone returned no UTC offset")
        return offset
