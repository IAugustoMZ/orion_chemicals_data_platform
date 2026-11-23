"""Render the declared naming variations and five source-specific dialects."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from tssource.domain.naming.metadata import describe
from tssource.domain.naming.plant_points import CataloguePoint
from tssource.domain.time.site_zone import SiteCode


class Variation(StrEnum):
    """Classify an introduced difference from the canonical tag name."""

    DROPPED_AREA = "dropped_area"
    SEPARATOR = "changed_separator"
    CASE = "changed_case"
    GLUED_LOOP = "glued_equipment_loop"
    LEGACY_ABBREVIATION = "legacy_abbreviation"
    SUFFIX = "changed_signal_suffix"
    NUMERIC = "numeric_only"
    FREE_TEXT = "free_text"
    TYPO = "typo"
    RENAME = "legacy_rename"
    CROSS_SITE_ALIAS = "cross_site_alias"


_DIALECT_VARIATIONS = (
    Variation.DROPPED_AREA,
    Variation.SEPARATOR,
    Variation.CASE,
    Variation.GLUED_LOOP,
    Variation.LEGACY_ABBREVIATION,
    Variation.SUFFIX,
)
AD_HOC_VARIATIONS = (Variation.NUMERIC, Variation.FREE_TEXT, Variation.TYPO, Variation.RENAME)
COVERAGE_VARIATIONS = (*_DIALECT_VARIATIONS, *AD_HOC_VARIATIONS)


@dataclass(frozen=True, slots=True)
class Dialect:
    """Define a site's separators, old site abbreviation and preferred changes."""

    separator: str
    legacy_prefix: str
    preferred: Variation

    @property
    def variations(self) -> tuple[Variation, ...]:
        """Try the preferred dialect form before other eligible changes."""
        return (
            self.preferred,
            *(kind for kind in _DIALECT_VARIATIONS if kind is not self.preferred),
        )


DIALECTS = {
    SiteCode.BRAZIL: Dialect("_", "BRZ", Variation.SEPARATOR),
    SiteCode.US_GULF_COAST: Dialect("/", "USGC", Variation.GLUED_LOOP),
    SiteCode.BELGIUM: Dialect("-", "BE", Variation.LEGACY_ABBREVIATION),
    SiteCode.CHINA: Dialect(":", "CN", Variation.DROPPED_AREA),
    SiteCode.INDIA: Dialect("_", "IN", Variation.CASE),
}
_SUFFIXES = {"PV": "VALUE", "SP": "SET", "OUT": "OUTPUT", "MODE": "STATE", "ALM": "ALARM"}


@dataclass(frozen=True, slots=True)
class TagSpelling:
    """Carry the current variation and optional previous name for one point."""

    current: str
    variation: Variation
    old_alias: str | None = None


def render_variation(point: CataloguePoint, variation: Variation) -> TagSpelling | None:
    """Propose a spelling or return None when the variation requires a signal."""
    name = point.canonical.render()
    if variation is Variation.RENAME:
        return TagSpelling(f"MIG.{name}", variation, old_alias=f"LEGACY.{name}")
    current = _SPELLINGS[variation](point, name)
    return None if current is None else TagSpelling(current, variation)


def _drop_area(point: CataloguePoint, name: str) -> str:
    """Remove the area segment while keeping the rest of the identifier."""
    return name.replace(f".{point.canonical.area}.", ".", 1)


def _separate(point: CataloguePoint, name: str) -> str:
    """Replace dots with the site's separator."""
    return name.replace(".", DIALECTS[point.canonical.site_code].separator)


def _lowercase(point: CataloguePoint, name: str) -> str:
    """Render the name in lowercase."""
    return name.lower()


def _glue_loop(point: CataloguePoint, name: str) -> str | None:
    """Fuse the equipment and instrument segments for an operational point."""
    canonical = point.canonical
    if canonical.signal is None:
        return None
    return name.replace(f".{canonical.equipment}.", f".{canonical.equipment}", 1)


def _legacy_prefix(point: CataloguePoint, name: str) -> str:
    """Use the site's legacy abbreviation."""
    canonical = point.canonical
    return f"{DIALECTS[canonical.site_code].legacy_prefix}.{canonical.local_name}"


def _suffix(point: CataloguePoint, name: str) -> str | None:
    """Use the local signal alias for an operational point."""
    signal = point.canonical.signal
    return None if signal is None else f"{name.rsplit('.', 1)[0]}.{_SUFFIXES[signal]}"


def _numeric(point: CataloguePoint, name: str) -> str:
    """Use the stable point ordinal as a zero-padded legacy identifier."""
    return f"{point.ordinal:08d}"


def _free_text(point: CataloguePoint, name: str) -> str:
    """Write a site-language label with the equipment and point codes for disambiguation."""
    canonical = point.canonical
    label = describe(point.instrument.measurement, canonical.site_code)
    return f"{label} / {name.split('.', 1)[0]} {canonical.equipment} {point.instrument.code}"


def _transpose(point: CataloguePoint, name: str) -> str:
    """Simulate a transposition at the beginning of the identifier."""
    return f"{name[1]}{name[0]}{name[2:]}"


def _shared_alias(point: CataloguePoint, name: str) -> str:
    """Use the part of the name shared by identical local names at different sites."""
    return point.canonical.local_name


_SPELLINGS: dict[Variation, Callable[[CataloguePoint, str], str | None]] = {
    Variation.DROPPED_AREA: _drop_area,
    Variation.SEPARATOR: _separate,
    Variation.CASE: _lowercase,
    Variation.GLUED_LOOP: _glue_loop,
    Variation.LEGACY_ABBREVIATION: _legacy_prefix,
    Variation.SUFFIX: _suffix,
    Variation.NUMERIC: _numeric,
    Variation.FREE_TEXT: _free_text,
    Variation.TYPO: _transpose,
    Variation.CROSS_SITE_ALIAS: _shared_alias,
}
