"""Verify private plant inventory, identity, topology and sampling policies."""

from collections import Counter

import pytest

from tssource.domain.plant.builder import PlantBuilder

SITE_TARGETS = {"brazil": 700, "us-gulf-coast": 450, "belgium": 350, "china": 350, "india": 200}


@pytest.mark.ac("PBI-004-01:AC1")
def test_inventory_reconciles() -> None:
    """Count the actual points by site, scan class and equipment class."""
    plant = PlantBuilder().build(42)
    sites = {site.id: site.code for site in plant.sites}
    areas = {area.id: sites[area.site_id] for area in plant.areas}
    equipment = {unit.id: unit for unit in plant.equipment}
    counts = Counter(
        (areas[equipment[point.equipment_id].area_id], point.scan_class)
        for point in plant.instruments
    )
    assert set(sites.values()) == SITE_TARGETS.keys()
    for site, target in SITE_TARGETS.items():
        count = sum(count for (code, _), count in counts.items() if code == site)
        assert target * 0.9 <= count <= target * 1.1
    classes = Counter(equipment[point.equipment_id].equipment_class for point in plant.instruments)
    assert classes.keys() == {
        "reactor",
        "column",
        "heat_exchanger",
        "pump",
        "compressor",
        "tank",
        "furnace",
        "separator",
        "valve_station",
        "analyser_house",
    }
    assert min(classes.values()) >= 10
    assert 90 <= sum(count for (_, scan), count in counts.items() if scan == "lab") <= 110
    assert len(plant.inventory) == len(counts)
    assert counts == {(row.site_code, row.scan_class): row.count for row in plant.inventory}


@pytest.mark.ac("PBI-004-01:AC2")
@pytest.mark.parametrize("seed", [0, 42, 101])
def test_same_seed_reproduces_the_model(seed: int) -> None:
    """Reproduce every immutable value and its order."""
    assert PlantBuilder().build(seed) == PlantBuilder().build(seed)


@pytest.mark.ac("PBI-004-01:AC3")
def test_different_seeds_change_ids() -> None:
    """Keep inventory shape while changing each corresponding surrogate."""
    first, second = PlantBuilder().build(0), PlantBuilder().build(101)
    assert first.inventory == second.inventory
    for before, after in zip(first.equipment, second.equipment, strict=True):
        assert before.equipment_class == after.equipment_class
        assert before.id != after.id
    for point, other in zip(first.instruments, second.instruments, strict=True):
        assert point.measurement == other.measurement
        assert point.id != other.id


@pytest.mark.ac("PBI-004-01:AC4")
def test_topology_resolves_in_each_area() -> None:
    """Resolve loop roles, stream endpoints and shared drivers by identifier."""
    plant = PlantBuilder().build(101)
    equipment = {unit.id: unit for unit in plant.equipment}
    points = {point.id: point for point in plant.instruments}
    drivers = {driver.id: driver for driver in plant.drivers}
    assert len(points) == len(plant.instruments)
    assert len(equipment) == len(plant.equipment)
    assert plant.control_loops and plant.streams and plant.drivers
    for loop in plant.control_loops:
        roles = (loop.measurement_id, loop.controller_id, loop.final_element_id)
        assert len(set(roles)) == 3
        assert all(equipment[points[role].equipment_id].area_id == loop.area_id for role in roles)
    for stream in plant.streams:
        assert stream.source_equipment_id != stream.target_equipment_id
        assert equipment[stream.source_equipment_id].area_id == stream.area_id
        assert equipment[stream.target_equipment_id].area_id == stream.area_id
    for unit in plant.equipment:
        assert drivers[unit.driver_id].area_id == unit.area_id
    assert min(Counter(unit.driver_id for unit in plant.equipment).values()) > 1


@pytest.mark.ac("PBI-004-01:AC5")
def test_scan_policy_matches_interval() -> None:
    """Check all seven periodic policies and both nonperiodic policies."""
    expected = {f"periodic_{seconds}s": seconds for seconds in (1, 5, 10, 30, 60, 300, 900)}
    expected.update({"lab": None, "report_by_exception": None})
    plant = PlantBuilder().build(42)
    assert {point.scan_class: point.expected_interval_seconds for point in plant.instruments} == (
        expected
    )
    for point in plant.instruments:
        assert point.expected_interval_seconds == expected[point.scan_class]
        assert point.range_min < point.range_max
