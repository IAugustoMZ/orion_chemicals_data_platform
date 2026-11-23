"""Assemble the default plant deterministically without I/O or random state."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise
from json import dumps

from tssource.domain.errors import TssourceError
from tssource.domain.plant.model import (
    Area,
    ControlLoop,
    Driver,
    Equipment,
    Instrument,
    InventoryCount,
    Plant,
    ScanClass,
    Site,
    Stream,
)
from tssource.domain.plant.profiles import EQUIPMENT_TEMPLATES, SITE_PROFILES, EquipmentTemplate
from tssource.domain.time.site_zone import SiteCode


@dataclass(frozen=True, slots=True)
class _SiteIdentity:
    """Scope stable surrogate identifiers to one seed and site."""

    seed: int
    site: SiteCode

    def make(self, kind: str, *path: str) -> str:
        """Hash a versioned sequence with explicit boundaries between path segments."""
        payload = dumps(("tssource-plant-v1", hex(self.seed), kind, self.site, path))
        return sha256(payload.encode("ascii")).hexdigest()


class PlantBuilder:
    """Construct the fixed site profiles in declaration order for a nonnegative seed."""

    def build(self, seed: int) -> Plant:
        """Generate the sites, relationships and matching scan-class counts."""
        if seed < 0:
            raise TssourceError("plant seed must be nonnegative")

        sites: list[Site] = []
        areas: list[Area] = []
        equipment: list[Equipment] = []
        instruments: list[Instrument] = []
        loops: list[ControlLoop] = []
        streams: list[Stream] = []
        drivers: list[Driver] = []
        counts: list[InventoryCount] = []
        for profile in SITE_PROFILES:
            ids = _SiteIdentity(seed, profile.site_code)
            site = Site(ids.make("site"), profile.site_code)
            sites.append(site)
            first_point = len(instruments)
            ordinal = 0
            for area_number, unit_count in enumerate(profile.units_by_area, start=1):
                area_path = str(area_number)
                area = Area(ids.make("area", area_path), site.id, f"A{area_number * 100}")
                driver = Driver(ids.make("driver", area_path), area.id, "area_load")
                areas.append(area)
                drivers.append(driver)
                first_unit = len(equipment)
                for unit_number in range(1, unit_count + 1):
                    template = EQUIPMENT_TEMPLATES[ordinal % len(EQUIPMENT_TEMPLATES)]
                    unit_path = (area_path, str(unit_number))
                    unit = Equipment(
                        ids.make("equipment", *unit_path),
                        area.id,
                        driver.id,
                        template.equipment_class,
                        f"{template.prefix}{area_number * 100 + unit_number}",
                    )
                    equipment.append(unit)
                    points = _points(ids, unit, unit_path, template)
                    instruments.extend(points.values())
                    if template.loop_roles is not None:
                        measurement, controller, final_element = template.loop_roles
                        loops.append(
                            ControlLoop(
                                ids.make("loop", *unit_path),
                                area.id,
                                points[measurement].id,
                                points[controller].id,
                                points[final_element].id,
                            )
                        )
                    ordinal += 1
                for index, (source, target) in enumerate(
                    pairwise(equipment[first_unit:]), start=1
                ):
                    streams.append(
                        Stream(
                            ids.make("stream", area_path, str(index)),
                            area.id,
                            source.id,
                            target.id,
                        )
                    )
            site_counts = Counter(point.scan_class for point in instruments[first_point:])
            counts.extend(
                InventoryCount(site.code, scan_class, site_counts[scan_class])
                for scan_class in ScanClass
                if site_counts[scan_class]
            )
        plant = Plant(
            tuple(sites),
            tuple(areas),
            tuple(equipment),
            tuple(instruments),
            tuple(loops),
            tuple(streams),
            tuple(drivers),
            tuple(counts),
        )
        _validate_relationships(plant)
        return plant


def _points(
    ids: _SiteIdentity, unit: Equipment, path: tuple[str, str], template: EquipmentTemplate
) -> dict[str, Instrument]:
    """Bind each ordered template point to equipment and its stable ID."""
    return {
        point.code: Instrument(
            ids.make("point", *path, point.code),
            unit.id,
            point.code,
            point.measurement,
            point.canonical_unit,
            point.data_type,
            point.range_min,
            point.range_max,
            point.scan_class,
        )
        for point in template.points
    }


def _validate_relationships(plant: Plant) -> None:
    """Resolve the area of each role, endpoint and driver before publishing."""
    equipment_areas = {unit.id: unit.area_id for unit in plant.equipment}
    point_areas = {point.id: equipment_areas[point.equipment_id] for point in plant.instruments}
    driver_areas = {driver.id: driver.area_id for driver in plant.drivers}
    for loop in plant.control_loops:
        roles = (loop.measurement_id, loop.controller_id, loop.final_element_id)
        if len(set(roles)) != 3 or any(point_areas.get(role) != loop.area_id for role in roles):
            raise TssourceError("plant loop has invalid point roles")
    for stream in plant.streams:
        endpoints = (stream.source_equipment_id, stream.target_equipment_id)
        if endpoints[0] == endpoints[1] or any(
            equipment_areas.get(unit_id) != stream.area_id for unit_id in endpoints
        ):
            raise TssourceError("plant stream has invalid equipment endpoints")
    for unit in plant.equipment:
        if driver_areas.get(unit.driver_id) != unit.area_id:
            raise TssourceError("plant equipment has an invalid driver reference")
