"""Declared fictional sites and their IANA civil-time zones."""

from __future__ import annotations

from dataclasses import dataclass
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
    """Bind a source site to its declared IANA zone without performing lookup I/O."""

    code: SiteCode
    zone_name: str


SITE_ZONES: dict[SiteCode, SiteZone] = {
    SiteCode.BRAZIL: SiteZone(SiteCode.BRAZIL, "America/Sao_Paulo"),
    SiteCode.US_GULF_COAST: SiteZone(SiteCode.US_GULF_COAST, "America/Chicago"),
    SiteCode.BELGIUM: SiteZone(SiteCode.BELGIUM, "Europe/Brussels"),
    SiteCode.CHINA: SiteZone(SiteCode.CHINA, "Asia/Shanghai"),
    SiteCode.INDIA: SiteZone(SiteCode.INDIA, "Asia/Kolkata"),
}
