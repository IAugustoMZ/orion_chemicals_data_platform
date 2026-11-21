"""Declared fictional sites and their civil-time policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum


class SiteCode(StrEnum):
    """The fixed fictional source sites accepted by the time core."""

    BRAZIL = "brazil"
    US_GULF_COAST = "us-gulf-coast"
    BELGIUM = "belgium"
    CHINA = "china"
    INDIA = "india"


@dataclass(frozen=True)
class SiteZone:
    """Bind a source site to its named zone or declared fixed offset."""

    code: SiteCode
    zone_name: str
    fixed_offset: timedelta | None = None


SITE_ZONES: dict[SiteCode, SiteZone] = {
    SiteCode.BRAZIL: SiteZone(SiteCode.BRAZIL, "America/Sao_Paulo"),
    SiteCode.US_GULF_COAST: SiteZone(SiteCode.US_GULF_COAST, "America/Chicago"),
    SiteCode.BELGIUM: SiteZone(SiteCode.BELGIUM, "Europe/Brussels"),
    SiteCode.CHINA: SiteZone(SiteCode.CHINA, "Asia/Shanghai", timedelta(hours=8)),
    SiteCode.INDIA: SiteZone(SiteCode.INDIA, "Asia/Kolkata", timedelta(hours=5, minutes=30)),
}
