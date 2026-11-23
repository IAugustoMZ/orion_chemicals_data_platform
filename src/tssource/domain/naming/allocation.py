"""Allocate unique names, reserved collisions and coverage floors in seeded order."""

from collections import defaultdict
from collections.abc import Iterable

from tssource.domain.errors import TssourceError
from tssource.domain.naming.plant_points import CataloguePoint
from tssource.domain.naming.violations import (
    AD_HOC_VARIATIONS,
    COVERAGE_VARIATIONS,
    DIALECTS,
    TagSpelling,
    Variation,
    render_variation,
)
from tssource.domain.time.site_zone import SiteCode

_VARIATION_MINIMUM = 20
_COLLISION_MINIMUM = 15
_CONVENTION_MINIMUM = 1000


class _Allocation:
    """Reserve source-scoped current and previous keys while assigning spellings."""

    def __init__(self, points: tuple[CataloguePoint, ...]) -> None:
        """Protect every canonical key up front, including future convention rows."""
        self.keys = {(point.canonical.site_code, point.canonical.render()) for point in points}
        self.spellings: dict[int, TagSpelling] = {}

    def reserve(self, point: CataloguePoint, spelling: TagSpelling) -> bool:
        """Reserve a point and its names together if all keys are available."""
        if point.ordinal in self.spellings:
            return False
        site = point.canonical.site_code
        keys = {(site, spelling.current)}
        if spelling.old_alias is not None:
            keys.add((site, spelling.old_alias))
        if not self.keys.isdisjoint(keys):
            return False
        self.keys.update(keys)
        self.spellings[point.ordinal] = spelling
        return True

    def assign(self, point: CataloguePoint, candidates: Iterable[Variation]) -> bool:
        """Take the first available spelling from a bounded candidate set."""
        if point.ordinal in self.spellings:
            return False
        for candidate in candidates:
            spelling = render_variation(point, candidate)
            if spelling is not None and self.reserve(point, spelling):
                return True
        return False


def allocate(points: tuple[CataloguePoint, ...]) -> dict[int, TagSpelling]:
    """Meet the declared floors before filling the remaining tier quotas."""
    dialect_target = round(len(points) * 0.25)
    ad_hoc_target = round(len(points) * 0.15)
    if len(points) - dialect_target - ad_hoc_target < _CONVENTION_MINIMUM:
        raise TssourceError("catalogue capacity is too small for the canonical name floor")

    allocation = _Allocation(points)
    dialect_count = _reserve_collisions(points, allocation)
    ad_hoc_count = 0
    for variation in COVERAGE_VARIATIONS:
        _reserve_variation_floor(points, allocation, variation)
        if variation in AD_HOC_VARIATIONS:
            ad_hoc_count += _VARIATION_MINIMUM
        else:
            dialect_count += _VARIATION_MINIMUM

    _fill(points, allocation, dialect_target - dialect_count, dialect=True)
    _fill(points, allocation, ad_hoc_target - ad_hoc_count, dialect=False)
    return allocation.spellings


def _reserve_collisions(points: tuple[CataloguePoint, ...], allocation: _Allocation) -> int:
    """Reserve a shared local spelling for two distinct sites and equipment IDs."""
    groups: dict[str, dict[SiteCode, CataloguePoint]] = defaultdict(dict)
    for point in points:
        groups[point.canonical.local_name].setdefault(point.canonical.site_code, point)

    pairs = 0
    for local_name, sites in groups.items():
        if len(sites) < 2:
            continue
        first, second, *_ = sites.values()
        if first.instrument.equipment_id == second.instrument.equipment_id:
            continue
        spelling = TagSpelling(local_name, Variation.CROSS_SITE_ALIAS)
        if not allocation.reserve(first, spelling) or not allocation.reserve(second, spelling):
            raise TssourceError("catalogue has conflicting cross-site aliases")
        pairs += 1
        if pairs == _COLLISION_MINIMUM:
            return pairs * 2
    raise TssourceError("catalogue capacity cannot supply the required cross-site collisions")


def _reserve_variation_floor(
    points: tuple[CataloguePoint, ...], allocation: _Allocation, variation: Variation
) -> None:
    """Select distinct usable points for one variation before filling tiers."""
    remaining = _VARIATION_MINIMUM
    for point in points:
        if allocation.assign(point, (variation,)):
            remaining -= 1
            if remaining == 0:
                return
    raise TssourceError(f"catalogue capacity cannot supply the {variation.value} floor")


def _fill(
    points: tuple[CataloguePoint, ...], allocation: _Allocation, remaining: int, *, dialect: bool
) -> None:
    """Fill the quota in one pass while testing a fixed set of spelling alternatives."""
    for index, point in enumerate(points):
        if remaining == 0:
            return
        if dialect:
            candidates = DIALECTS[point.canonical.site_code].variations
        else:
            offset = index % len(AD_HOC_VARIATIONS)
            candidates = (*AD_HOC_VARIATIONS[offset:], *AD_HOC_VARIATIONS[:offset])
        if allocation.assign(point, candidates):
            remaining -= 1
    if remaining:
        raise TssourceError("catalogue capacity cannot fill the requested naming tiers")
