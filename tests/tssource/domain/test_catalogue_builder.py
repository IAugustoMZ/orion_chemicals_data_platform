"""Verify source-scoped identity, coverage, metadata and reproducibility."""

from collections import Counter, defaultdict
from dataclasses import fields, replace
from datetime import UTC, datetime

import pytest

from tssource.bootstrap import build_catalogue_builder
from tssource.domain.errors import TssourceError
from tssource.domain.naming.catalogue_builder import CatalogueBuilder
from tssource.domain.naming.convention import CanonicalName
from tssource.domain.naming.draws import DrawDomain
from tssource.domain.naming.model import Catalogue, NamingTier
from tssource.domain.naming.violations import Variation
from tssource.domain.plant.builder import PlantBuilder
from tssource.domain.time.site_zone import SiteCode


class OrderedDraws:
    """Supply a deterministic identity permutation to test the pure rules."""

    def order(self, domain: DrawDomain, size: int) -> tuple[int, ...]:
        """Return each index exactly once."""
        return tuple(range(size))


@pytest.fixture(scope="module")
def catalogue() -> Catalogue:
    """Use the merged plant and an injected draw source to exercise allocation."""
    return CatalogueBuilder(OrderedDraws()).build(PlantBuilder().build(42))


@pytest.mark.ac("PBI-004-02:AC2")
def test_tiers_and_canonical_names(catalogue: Catalogue) -> None:
    """Check distribution, unique canonical keys and the canonical-name floor."""
    references = catalogue.references
    names = {reference.canonical_name for reference in references}
    assert len(names) == len(references)
    tiers = Counter(reference.tier for reference in references)
    assert tiers[NamingTier.CONVENTION] >= 1000
    for tier, share in zip(NamingTier, (0.60, 0.25, 0.15), strict=True):
        assert tiers[tier] / len(references) == pytest.approx(share, abs=0.05)
    for row in references:
        assert CanonicalName.parse(row.canonical_name).site_code is row.site_code
        if row.tier is NamingTier.CONVENTION:
            assert row.original_name == row.canonical_name and row.violations == ()


@pytest.mark.ac("PBI-004-02:AC3")
def test_each_variation_has_distinct_examples(catalogue: Catalogue) -> None:
    """Verify the declared variation coverage and that the original name really changes."""
    instruments_by_variation: dict[Variation, set[str]] = defaultdict(set)
    for row in catalogue.references:
        for variation in row.violations:
            assert row.original_name != row.canonical_name
            instruments_by_variation[variation].add(row.instrument_id)
    assert set(instruments_by_variation) == set(Variation)
    assert min(map(len, instruments_by_variation.values())) >= 20


@pytest.mark.ac("PBI-004-02:AC4")
def test_cross_site_collisions_have_distinct_equipment(catalogue: Catalogue) -> None:
    """Group by original name and check both sides of each collision."""
    references_by_name = defaultdict(list)
    for row in catalogue.references:
        references_by_name[row.original_name].append(row)
    collisions = [rows for rows in references_by_name.values() if len(rows) > 1]
    assert len(collisions) >= 15
    for group in collisions:
        assert len({row.site_code for row in group}) == len(group)
        assert len({row.equipment_id for row in group}) == len(group)


@pytest.mark.ac("PBI-004-02:AC5")
def test_unique_join_and_plant_ids(catalogue: Catalogue) -> None:
    """Join every point back to its source, equipment, plant policy and explicit loop."""
    plant = PlantBuilder().build(42)
    points = {point.id: point for point in plant.instruments}
    equipment = {unit.id: unit for unit in plant.equipment}
    areas = {area.id: area for area in plant.areas}
    sites = {site.id: site.code for site in plant.sites}
    loop_by_point = {
        point: loop.id
        for loop in plant.control_loops
        for point in (loop.measurement_id, loop.controller_id, loop.final_element_id)
    }
    keys = {(row.site_code, row.original_name) for row in catalogue.records}
    assert {field.name for field in fields(catalogue.records[0])} == {
        "site_code",
        "original_name",
        "descriptor",
        "reported_unit",
        "data_type",
        "scan_class",
        "expected_interval_seconds",
        "generator",
    }
    assert len(keys) == len(catalogue.records) == len(plant.instruments)
    assert {row.instrument_id for row in catalogue.references} == points.keys()
    assert len(catalogue.references) == len(keys)
    for record, reference in zip(catalogue.records, catalogue.references, strict=True):
        point = points[reference.instrument_id]
        assert point.equipment_id == reference.equipment_id
        assert record.site_code == sites[areas[equipment[point.equipment_id].area_id].site_id]
        assert reference.loop_id == loop_by_point.get(point.id)
        assert reference.canonical_unit == point.canonical_unit
        assert reference.measurement == point.measurement
        assert (record.site_code, record.original_name) == (
            reference.site_code,
            reference.original_name,
        )
        assert (record.data_type, record.scan_class, record.expected_interval_seconds) == (
            point.data_type,
            point.scan_class,
            point.expected_interval_seconds,
        )


@pytest.mark.ac("PBI-004-02:AC6")
def test_metadata_uses_site_vocabulary_and_introduces_missing_values(catalogue: Catalogue) -> None:
    """Check descriptor language distribution and both metadata floors."""
    rows, refs = catalogue.records, catalogue.references
    assert sum(not row.descriptor for row in rows) / len(rows) >= 0.05
    assert (
        sum(row.reported_unit != ref.canonical_unit for row, ref in zip(rows, refs, strict=True))
        / len(rows)
        >= 0.05
    )
    assert all(
        row.descriptor.endswith(" measurement")
        for row in rows
        if row.descriptor and row.site_code is not SiteCode.BRAZIL
    )
    assert all(
        row.descriptor.startswith("Medição de ")
        for row in rows
        if row.descriptor and row.site_code is SiteCode.BRAZIL
    )


@pytest.mark.ac("PBI-004-02:AC7")
@pytest.mark.parametrize("seed", [0, 42, 101])
def test_composed_catalogue_repeats_with_one_holdout_site(seed: int) -> None:
    """Prove repeatability with fresh production draw adapters."""
    plant = PlantBuilder().build(seed)
    builder = build_catalogue_builder(seed)
    output = builder.build(plant)
    assert output == builder.build(plant)
    assert output == build_catalogue_builder(seed).build(PlantBuilder().build(seed))
    holdout_sites = {row.site_code for row in output.references if row.holdout}
    assert len(holdout_sites) == 1
    assert all(row.holdout == (row.site_code in holdout_sites) for row in output.references)


@pytest.mark.ac("PBI-004-02:AC8")
def test_renamed_tags_retain_private_history(catalogue: Catalogue) -> None:
    """Retain an unambiguous old alias without publishing it as a current name."""
    current = {(row.site_code, row.original_name) for row in catalogue.records}
    aliases = set()
    for row in catalogue.references:
        if Variation.RENAME in row.violations:
            assert row.old_alias and (row.site_code, row.old_alias) not in current
            assert row.replaced_at == datetime(2025, 1, 1, tzinfo=UTC)
            aliases.add((row.site_code, row.old_alias))
        else:
            assert row.old_alias is row.replaced_at is None
    assert len(aliases) >= 20


def test_builder_rejects_duplicate_points_and_insufficient_profiles() -> None:
    """Reject input that cannot supply one valid record per point or meet the floors."""
    plant = PlantBuilder().build(42)
    builder = CatalogueBuilder(OrderedDraws())
    with pytest.raises(TssourceError, match="duplicate"):
        builder.build(replace(plant, instruments=(plant.instruments[0], *plant.instruments)))
    conflicting = replace(plant.instruments[0], id="different-point-id")
    with pytest.raises(TssourceError, match="duplicate canonical"):
        builder.build(replace(plant, instruments=(*plant.instruments, conflicting)))
    with pytest.raises(TssourceError, match="capacity"):
        builder.build(replace(plant, instruments=plant.instruments[:100]))
