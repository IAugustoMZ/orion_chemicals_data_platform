"""Derive consumer tags and their private references from the same ordered plant."""

from datetime import UTC, datetime
from math import ceil

from tssource.domain.naming.allocation import allocate
from tssource.domain.naming.draws import DrawDomain, DrawSource
from tssource.domain.naming.metadata import alternate_unit, describe
from tssource.domain.naming.model import Catalogue, ConsumerTag, NamingTier, ReferenceTag
from tssource.domain.naming.plant_points import CataloguePoint, resolve_points
from tssource.domain.naming.violations import AD_HOC_VARIATIONS, TagSpelling
from tssource.domain.plant.model import Plant
from tssource.domain.time.site_zone import SiteCode

_REPLACED_AT = datetime(2025, 1, 1, tzinfo=UTC)
_METADATA_FLOOR = 0.05


class CatalogueBuilder:
    """Generate the two row sets using injected and independently seeded decisions."""

    def __init__(self, draws: DrawSource) -> None:
        """Receive deterministic permutations without depending on a numeric library."""
        self._draws = draws

    def build(self, plant: Plant) -> Catalogue:
        """Allocate spellings and project each point into aligned current and private rows."""
        points = resolve_points(plant)
        size = len(points)
        order = self._draws.order(DrawDomain.VARIANTS, size)
        spellings = allocate(tuple(points[index] for index in order))
        metadata_count = ceil(size * _METADATA_FLOOR)
        missing_descriptors = set(self._draws.order(DrawDomain.DESCRIPTORS, size)[:metadata_count])
        unit_variants = self._draws.order(DrawDomain.UNITS, size)[:metadata_count]
        empty_units = set(unit_variants[::2])
        alternate_units = set(unit_variants[1::2])
        sites = tuple(site.code for site in plant.sites)
        holdout = sites[self._draws.order(DrawDomain.HOLDOUT, len(sites))[0]]

        records: list[ConsumerTag] = []
        references: list[ReferenceTag] = []
        for index, point in enumerate(points):
            instrument = point.instrument
            site = point.canonical.site_code
            descriptor = (
                "" if index in missing_descriptors else describe(instrument.measurement, site)
            )
            reported_unit = instrument.canonical_unit
            if index in empty_units:
                reported_unit = ""
            elif index in alternate_units:
                reported_unit = alternate_unit(reported_unit)
            reference = _reference(point, spellings.get(point.ordinal), holdout)
            records.append(
                ConsumerTag(
                    site,
                    reference.original_name,
                    descriptor,
                    reported_unit,
                    instrument.data_type,
                    instrument.scan_class,
                    instrument.expected_interval_seconds,
                )
            )
            references.append(reference)
        return Catalogue(tuple(records), tuple(references))


def _reference(
    point: CataloguePoint, spelling: TagSpelling | None, holdout: SiteCode
) -> ReferenceTag:
    """Keep private fixture labels and history alongside the shared current key."""
    site = point.canonical.site_code
    canonical = point.canonical.render()
    instrument = point.instrument
    tier = NamingTier.CONVENTION
    if spelling is not None:
        tier = NamingTier.AD_HOC if spelling.variation in AD_HOC_VARIATIONS else NamingTier.DIALECT
    old_alias = spelling.old_alias if spelling is not None else None
    return ReferenceTag(
        site_code=site,
        original_name=canonical if spelling is None else spelling.current,
        equipment_id=instrument.equipment_id,
        instrument_id=instrument.id,
        loop_id=point.loop_id,
        measurement=instrument.measurement,
        canonical_unit=instrument.canonical_unit,
        canonical_name=canonical,
        tier=tier,
        violations=() if spelling is None else (spelling.variation,),
        holdout=site is holdout,
        old_alias=old_alias,
        replaced_at=None if old_alias is None else _REPLACED_AT,
    )
