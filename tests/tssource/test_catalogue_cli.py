"""Exercise catalogue publication through the CLI and reconcile it with plant truth."""

import json
import stat
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner, Result

from tssource.bootstrap import build_catalogue_builder
from tssource.domain.errors import TssourceError
from tssource.domain.plant.builder import PlantBuilder
from tssource.infrastructure.catalogue_parquet import CatalogueParquetWriter
from tssource.interfaces.cli.app import app

runner = CliRunner()
PUBLIC = Path("catalog/tags.parquet")
PRIVATE = Path("truth/tag_key.parquet")


def export(out: Path, seed: str = "42") -> Result:
    """Invoke the public catalogue entry point with explicit settings."""
    return runner.invoke(app, ["catalog", "build", "--out", str(out), "--seed", seed])


@pytest.mark.ac("PBI-004-03:AC1")
@pytest.mark.ac("PBI-004-03:AC2")
def test_exports_exact_versioned_schemas(tmp_path: Path) -> None:
    """Check publication paths, column contracts and private file access."""
    result = export(tmp_path)
    assert result.exit_code == 0, result.output
    assert result.stdout == f"{tmp_path / PUBLIC}\n{tmp_path / PRIVATE}\n"
    assert not result.stderr
    assert {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()} == {
        PUBLIC,
        PRIVATE,
    }
    assert stat.S_IMODE((tmp_path / PRIVATE).stat().st_mode) == 0o600
    public = pq.read_table(tmp_path / PUBLIC)
    assert public.schema == pa.schema(
        [
            pa.field("site_code", pa.string(), nullable=False),
            pa.field("original_name", pa.string(), nullable=False),
            pa.field("descriptor", pa.string(), nullable=False),
            pa.field("reported_unit", pa.string(), nullable=False),
            pa.field("data_type", pa.string(), nullable=False),
            pa.field("scan_class", pa.string(), nullable=False),
            pa.field("expected_interval_seconds", pa.int32()),
            pa.field("generator", pa.string(), nullable=False),
        ]
    )
    private = pq.read_table(tmp_path / PRIVATE)
    assert private.schema == pa.schema(
        [
            pa.field("site_code", pa.string(), nullable=False),
            pa.field("original_name", pa.string(), nullable=False),
            pa.field("equipment_id", pa.string(), nullable=False),
            pa.field("instrument_id", pa.string(), nullable=False),
            pa.field("loop_id", pa.string()),
            pa.field("measurement", pa.string(), nullable=False),
            pa.field("canonical_unit", pa.string(), nullable=False),
            pa.field("canonical_name", pa.string(), nullable=False),
            pa.field("tier", pa.string(), nullable=False),
            pa.field("violations", pa.list_(pa.string()), nullable=False),
            pa.field("holdout", pa.bool_(), nullable=False),
            pa.field("old_alias", pa.string()),
            pa.field("replaced_at", pa.timestamp("us", tz="UTC")),
        ]
    )
    assert public.schema.metadata == private.schema.metadata == {b"schema_version": b"1"}
    assert set(public["generator"].to_pylist()) == {"tssource"}


@pytest.mark.ac("PBI-004-03:AC3")
@pytest.mark.ac("PBI-004-03:AC4")
@pytest.mark.parametrize("seed", ["0", "42", "101"])
def test_exports_reconcile_with_same_seed_plant(tmp_path: Path, seed: str) -> None:
    """Check one-to-one keys, instrument links, counts and scan policies."""
    assert export(tmp_path, seed).exit_code == 0
    assert (
        runner.invoke(app, ["plant", "build", "--seed", seed, "--out", str(tmp_path)]).exit_code
        == 0
    )
    plant = json.loads((tmp_path / "truth/plant.json").read_text(encoding="utf-8"))
    points = {point["id"]: point for point in plant["instruments"]}
    areas = {area["id"]: area for area in plant["areas"]}
    equipment = {unit["id"]: unit for unit in plant["equipment"]}
    sites = {site["id"]: site for site in plant["sites"]}
    public = pq.read_table(tmp_path / PUBLIC).to_pylist()
    private = pq.read_table(tmp_path / PRIVATE).to_pylist()
    public_keys = {(row["site_code"], row["original_name"]) for row in public}
    by_key = {(row["site_code"], row["original_name"]): row for row in private}
    assert len(public) == len(public_keys) == len(private) == len(by_key) == len(points)
    assert public_keys == by_key.keys()
    assert {row["instrument_id"] for row in private} == points.keys()
    assert Counter((row["site_code"], row["scan_class"]) for row in public) == {
        (row["site_code"], row["scan_class"]): row["count"] for row in plant["inventory"]
    }
    for row in public:
        reference = by_key[row["site_code"], row["original_name"]]
        point = points[reference["instrument_id"]]
        assert reference["equipment_id"] == point["equipment_id"]
        area = areas[equipment[point["equipment_id"]]["area_id"]]
        assert row["site_code"] == sites[area["site_id"]]["code"]
        assert row["scan_class"] == point["scan_class"]
        assert row["expected_interval_seconds"] == point["expected_interval_seconds"]


@pytest.mark.ac("PBI-004-04:AC1")
def test_file_destination_reports_safe_staging_error(tmp_path: Path) -> None:
    """Handle a real filesystem failure without exposing the destination."""
    destination = tmp_path / "existing-file"
    destination.write_bytes(b"keep")
    result = export(destination)
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.strip() == "error: could not stage tags.parquet"
    assert destination.read_bytes() == b"keep"


@pytest.mark.ac("PBI-004-03:AC5")
@pytest.mark.ac("PBI-004-04:AC1")
@pytest.mark.parametrize("fail_in", [PUBLIC, PRIVATE])
@pytest.mark.parametrize("error_type", [OSError, pa.ArrowInvalid])
def test_failed_staging_preserves_previous_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_in: Path, error_type: type[Exception]
) -> None:
    """Fail either Parquet write and verify both previous files and cleanup."""
    assert export(tmp_path).exit_code == 0
    before = {path: (tmp_path / path).read_bytes() for path in (PUBLIC, PRIVATE)}
    write_table = pq.write_table

    def fail_stage(table: pa.Table, where: Path) -> None:
        """Inject an error containing the selected staging path."""
        if where.parent == tmp_path / fail_in.parent:
            where.write_bytes(b"partial")
            raise error_type(f"raw staging error in {where}")
        write_table(table, where)

    monkeypatch.setattr(pq, "write_table", fail_stage)
    result = export(tmp_path, "101")
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.strip() == f"error: could not stage {fail_in.name}"
    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


@pytest.mark.parametrize("duplicate", [True, False])
def test_writer_rejects_invalid_keys_before_staging(tmp_path: Path, duplicate: bool) -> None:
    """Reject duplicates and missing counterparts before writing to disk."""
    catalogue = build_catalogue_builder(42).build(PlantBuilder().build(42))
    references = catalogue.references[:-1]
    if duplicate:
        references += (references[0],)
    message = "duplicate source and name keys" if duplicate else "keys differ"
    with pytest.raises(TssourceError, match=message):
        CatalogueParquetWriter().write(replace(catalogue, references=references), tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("change_schema", [True, False])
def test_writer_rejects_inconsistent_staged_footer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change_schema: bool
) -> None:
    """Reject a readable staged file whose schema or row count differs."""
    write_table = pq.write_table

    def change_reference(table: pa.Table, where: Path) -> None:
        """Change only the second file so both stages must be cleaned up."""
        if where.parent.name == "truth":
            table = table.replace_schema_metadata(None) if change_schema else table.slice(1)
        write_table(table, where)

    monkeypatch.setattr(pq, "write_table", change_reference)
    result = export(tmp_path)
    assert result.exit_code == 1
    assert result.stdout == ""
    assert ("schema differs" if change_schema else "row count differs") in result.stderr
    assert not any(path.is_file() for path in tmp_path.rglob("*"))


@pytest.mark.ac("PBI-004-04:AC2")
@pytest.mark.parametrize("fail_in", [PUBLIC, PRIVATE])
def test_failed_replace_reports_safe_error_and_retry_restores_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_in: Path
) -> None:
    """Exercise an interrupted publication and a same-seed recovery."""
    assert export(tmp_path).exit_code == 0
    before = {path: (tmp_path / path).read_bytes() for path in (PUBLIC, PRIVATE)}
    replace = Path.replace

    def fail_replace(self: Path, target: Path) -> Path:
        """Inject a replacement failure containing both paths."""
        if target == tmp_path / fail_in:
            raise OSError(f"raw replacement error from {self} to {target}")
        return replace(self, target)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_replace)
        result = export(tmp_path, "101")
        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr.strip() == f"error: could not publish {fail_in.name}"
    assert (tmp_path / PRIVATE).read_bytes() == before[PRIVATE]
    assert ((tmp_path / PUBLIC).read_bytes() == before[PUBLIC]) == (fail_in == PUBLIC)
    assert export(tmp_path, "101").exit_code == 0
    public = pq.read_table(tmp_path / PUBLIC).to_pylist()
    private = pq.read_table(tmp_path / PRIVATE).to_pylist()
    assert {(row["site_code"], row["original_name"]) for row in public} == {
        (row["site_code"], row["original_name"]) for row in private
    }
    assert (tmp_path / PRIVATE).read_bytes() != before[PRIVATE]
    assert {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()} == {
        PUBLIC,
        PRIVATE,
    }


@pytest.mark.parametrize("relative", [PUBLIC.parent, PUBLIC, PRIVATE.parent, PRIVATE])
def test_symlinks_at_fixed_paths_are_rejected(tmp_path: Path, relative: Path) -> None:
    """Keep an external directory or file intact when an output component is a link."""
    other = tmp_path / "other"
    other.mkdir()
    existing = other / "existing"
    existing.write_bytes(b"keep")
    out = tmp_path / "output"
    linked = out / relative
    linked.parent.mkdir(parents=True)
    linked.symlink_to(other if relative.suffix == "" else existing)
    result = export(out)
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "symlink" in result.stderr
    assert list(other.iterdir()) == [existing]
    assert existing.read_bytes() == b"keep"


def test_settings_defaults_and_invalid_seed(tmp_path: Path) -> None:
    """Use environment defaults and reject negative flag and environment seeds."""
    env = {"TSSOURCE_OUT": str(tmp_path), "TSSOURCE_SEED": "101"}
    assert export(tmp_path, "-1").exit_code == 2
    assert (
        runner.invoke(app, ["catalog", "build"], env={**env, "TSSOURCE_SEED": "-1"}).exit_code == 2
    )
    assert not list(tmp_path.iterdir())
    (tmp_path / PRIVATE.parent).mkdir(mode=0o750)
    assert runner.invoke(app, ["catalog", "build"], env=env).exit_code == 0
    assert stat.S_IMODE((tmp_path / PRIVATE.parent).stat().st_mode) == 0o750
    first = (tmp_path / PRIVATE).read_bytes()
    assert export(tmp_path, "101").exit_code == 0
    assert (tmp_path / PRIVATE).read_bytes() == first
