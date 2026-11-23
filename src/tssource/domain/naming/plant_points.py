"""Resolve plant point context and derive canonical names from fixture definitions."""

from dataclasses import dataclass

from tssource.domain.errors import TssourceError
from tssource.domain.naming.convention import CanonicalName
from tssource.domain.plant.model import Area, Equipment, Instrument, Plant, ScanClass
from tssource.domain.time.site_zone import SiteCode

_CONTROL_SIGNALS = frozenset({"PV", "SP", "OUT", "MODE", "ALM"})
_CONTROL_INSTRUMENT = {"degC": "TIC", "m3/h": "FIC", "kPa": "PIC", "%": "LIC"}


@dataclass(frozen=True, slots=True)
class CataloguePoint:
    """Pair an instrument with its resolved name, loop and stable fixture ordinal."""

    instrument: Instrument
    canonical: CanonicalName
    loop_id: str | None
    ordinal: int


def resolve_points(plant: Plant) -> tuple[CataloguePoint, ...]:
    """Resolve ordered points by ID and turn inconsistent associations into handled errors."""
    sites = {site.id: site.code for site in plant.sites}
    areas = {area.id: area for area in plant.areas}
    equipment = {unit.id: unit for unit in plant.equipment}
    point_ids = {point.id for point in plant.instruments}
    if (
        len(point_ids) != len(plant.instruments)
        or len(equipment) != len(plant.equipment)
        or len(areas) != len(plant.areas)
        or len(sites) != len(plant.sites)
    ):
        raise TssourceError("catalogue plant has duplicate entity IDs")

    loops = _loop_membership(plant)
    primary_units = {
        point.equipment_id: point.canonical_unit
        for point in plant.instruments
        if point.code == "PV"
    }
    points = []
    try:
        for ordinal, point in enumerate(plant.instruments, start=1):
            unit = equipment[point.equipment_id]
            area = areas[unit.area_id]
            canonical = _canonical(sites[area.site_id], area, unit, point, primary_units)
            points.append(CataloguePoint(point, canonical, loops.get(point.id), ordinal))
    except (KeyError, ValueError) as error:
        raise TssourceError("catalogue plant has an invalid point association or name") from error

    if len({point.canonical for point in points}) != len(points):
        raise TssourceError("catalogue plant has duplicate canonical names")
    return tuple(points)


def _loop_membership(plant: Plant) -> dict[str, str]:
    """Index explicit loop roles and reject any point claimed by two loops."""
    membership: dict[str, str] = {}
    for loop in plant.control_loops:
        for point_id in (loop.measurement_id, loop.controller_id, loop.final_element_id):
            if point_id in membership:
                raise TssourceError("catalogue point has conflicting loop memberships")
            membership[point_id] = loop.id
    return membership


def _canonical(
    site: SiteCode, area: Area, unit: Equipment, point: Instrument, primary_units: dict[str, str]
) -> CanonicalName:
    """Map instrument roles and engineering units to canonical grammar tokens."""
    if point.scan_class is ScanClass.LAB:
        return CanonicalName(site, area.code, unit.code, point.code, None)
    if point.code in _CONTROL_SIGNALS:
        primary_unit = primary_units.get(unit.id)
        letters = "AI" if primary_unit is None else _CONTROL_INSTRUMENT[primary_unit]
        signal = point.code
    else:
        letters = "ZI" if point.code == "POS" else point.code
        signal = "PV"
    return CanonicalName(site, area.code, unit.code, f"{letters}-{unit.code[-3:]}0", signal)
