"""IANA ``zoneinfo`` adapter with explicit fold round-trip classification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from tssource.domain.time.resolution import LocalResolution, ResolutionStatus
from tssource.domain.time.site_zone import SiteZone


class ZoneInfoResolver:
    """Resolve declared local values through the standard-library IANA timezone database."""

    def resolve(self, site: SiteZone, local: datetime) -> LocalResolution:
        """Classify valid, repeated, and skipped local values using UTC round-trips."""
        if local.tzinfo is not None:
            raise ValueError("local time must be naive")
        zone = ZoneInfo(site.zone_name)
        candidates = self._candidates(zone, local)
        if not candidates:
            gap_candidates = self._first_valid(zone, local)
            return LocalResolution(
                local, ResolutionStatus.GAP, gap_candidates, self._offsets(zone, gap_candidates)
            )
        status = ResolutionStatus.OK if len(candidates) == 1 else ResolutionStatus.AMBIGUOUS
        return LocalResolution(local, status, candidates, self._offsets(zone, candidates))

    @staticmethod
    def _candidates(zone: ZoneInfo, local: datetime) -> tuple[datetime, ...]:
        """Return UTC folds that round-trip to exactly the requested local wall value."""
        values: set[datetime] = set()
        for fold in (0, 1):
            candidate = local.replace(tzinfo=zone, fold=fold).astimezone(UTC)
            if candidate.astimezone(zone).replace(tzinfo=None) == local:
                values.add(candidate)
        return tuple(sorted(values))

    def _first_valid(self, zone: ZoneInfo, local: datetime) -> tuple[datetime, ...]:
        """Advance a skipped local value to the first minute with a physical instant."""
        probe = local
        for _ in range(24 * 60):
            probe += timedelta(minutes=1)
            candidates = self._candidates(zone, probe)
            if candidates:
                return (candidates[0],)
        raise ValueError("no valid local time found within one day")

    @staticmethod
    def _offsets(zone: ZoneInfo, candidates: tuple[datetime, ...]) -> tuple[timedelta, ...]:
        """Retain the source offsets that led from each local fold to UTC."""
        return tuple(
            candidate.astimezone(zone).utcoffset() or timedelta() for candidate in candidates
        )
