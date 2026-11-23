"""Parse and render the Orion fixture's version 1 tag-name grammar."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tssource.domain.time.site_zone import SiteCode

SITE_PREFIXES = {
    SiteCode.BRAZIL: "ORN",
    SiteCode.US_GULF_COAST: "GUL",
    SiteCode.BELGIUM: "BEL",
    SiteCode.CHINA: "CHN",
    SiteCode.INDIA: "IND",
}
_SITES_BY_PREFIX = {prefix: site for site, prefix in SITE_PREFIXES.items()}
_AREA = r"A[1-9][0-9]{2}"
_UNIT = r"[A-Z]{1,2}[1-9][0-9]{2}"
_INSTRUMENT = r"(?:TIC|FIC|PIC|LIC|TI|PI|FI|EI|AI|QI|ZI)-[0-9]{4}"
_SIGNAL = r"PV|SP|OUT|MODE|ALM"
_ANALYTE = r"PH|H2O|CL|SOL|RHO"
_PROCESS = re.compile(rf"{_AREA}\.{_UNIT}\.{_INSTRUMENT}\.(?:{_SIGNAL})")
_LAB = re.compile(rf"LAB\.{_AREA}\.{_UNIT}\.(?:{_ANALYTE})")


@dataclass(frozen=True, slots=True)
class CanonicalName:
    """Represent either an operational point or a lab analyte if signal is absent."""

    site_code: SiteCode
    area: str
    equipment: str
    instrument: str
    signal: str | None

    def __post_init__(self) -> None:
        """Enforce the grammar for both constructed and parsed values."""
        pattern = _LAB if self.signal is None else _PROCESS
        if pattern.fullmatch(self.local_name) is None:
            raise ValueError("invalid canonical tag name")

    @property
    def local_name(self) -> str:
        """Render the canonical segments after the site prefix."""
        if self.signal is None:
            return f"LAB.{self.area}.{self.equipment}.{self.instrument}"
        return f"{self.area}.{self.equipment}.{self.instrument}.{self.signal}"

    def render(self) -> str:
        """Render the exact canonical spelling, including the site prefix."""
        return f"{SITE_PREFIXES[self.site_code]}.{self.local_name}"

    @classmethod
    def parse(cls, text: str) -> CanonicalName:
        """Parse only a complete, case-sensitive version 1 tag name."""
        parts = text.split(".")
        if len(parts) != 5 or parts[0] not in _SITES_BY_PREFIX:
            raise ValueError("invalid canonical tag name")
        prefix, first, second, third, fourth = parts
        site = _SITES_BY_PREFIX[prefix]
        if first == "LAB":
            return cls(site, second, third, fourth, None)
        return cls(site, first, second, third, fourth)
