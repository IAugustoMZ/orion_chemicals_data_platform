"""Keep consumer observations and evaluator-only tag reference values separate."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from tssource.domain.naming.violations import Variation
from tssource.domain.plant.model import ScanClass
from tssource.domain.time.site_zone import SiteCode


class NamingTier(StrEnum):
    """Classify a name as conventional, a site dialect or ad hoc."""

    CONVENTION = "convention"
    DIALECT = "dialect"
    AD_HOC = "ad_hoc"


@dataclass(frozen=True, slots=True)
class ConsumerTag:
    """Carry only the current source tag and its observed metadata."""

    site_code: SiteCode
    original_name: str
    descriptor: str
    reported_unit: str
    data_type: str
    scan_class: ScanClass
    expected_interval_seconds: int | None
    generator: str = "tssource"


@dataclass(frozen=True, slots=True)
class ReferenceTag:
    """Link a source-scoped tag to the private plant and synthetic naming history."""

    site_code: SiteCode
    original_name: str
    equipment_id: str
    instrument_id: str
    loop_id: str | None
    measurement: str
    canonical_unit: str
    canonical_name: str
    tier: NamingTier
    violations: tuple[Variation, ...]
    holdout: bool
    old_alias: str | None
    replaced_at: datetime | None


@dataclass(frozen=True, slots=True)
class Catalogue:
    """Hold aligned consumer and reference snapshots in plant instrument order."""

    records: tuple[ConsumerTag, ...]
    references: tuple[ReferenceTag, ...]
