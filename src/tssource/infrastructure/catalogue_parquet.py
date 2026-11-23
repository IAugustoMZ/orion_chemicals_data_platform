"""Publish the consumer and private catalogue projections as versioned Parquet files."""

import os
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import pyarrow as pa
import pyarrow.parquet as pq

from tssource.domain.errors import TssourceError
from tssource.domain.naming.model import Catalogue, ConsumerTag, ReferenceTag

_SCHEMA_METADATA = {b"schema_version": b"1"}
_CONSUMER_SCHEMA = pa.schema(
    [
        pa.field("site_code", pa.string(), nullable=False),
        pa.field("original_name", pa.string(), nullable=False),
        pa.field("descriptor", pa.string(), nullable=False),
        pa.field("reported_unit", pa.string(), nullable=False),
        pa.field("data_type", pa.string(), nullable=False),
        pa.field("scan_class", pa.string(), nullable=False),
        pa.field("expected_interval_seconds", pa.int32()),
        pa.field("generator", pa.string(), nullable=False),
    ],
    metadata=_SCHEMA_METADATA,
)
_REFERENCE_SCHEMA = pa.schema(
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
        pa.field("violations", pa.list_(pa.field("element", pa.string())), nullable=False),
        pa.field("holdout", pa.bool_(), nullable=False),
        pa.field("old_alias", pa.string()),
        pa.field("replaced_at", pa.timestamp("us", tz="UTC")),
    ],
    metadata=_SCHEMA_METADATA,
)


class CatalogueParquetWriter:
    """Stage both validated files before replacing either fixed destination."""

    def write(self, catalogue: Catalogue, output_folder: Path) -> tuple[Path, Path]:
        """Return both paths only after publication to the trusted folder succeeds."""
        consumer = output_folder / "catalog" / "tags.parquet"
        reference = output_folder / "truth" / "tag_key.parquet"
        _validate_keys(catalogue)
        with _safe_diagnostic("could not prepare or clean up catalogue files"):
            if any(
                path.parent.is_symlink() or path.is_symlink() for path in (consumer, reference)
            ):
                raise TssourceError(
                    "catalogue output refuses symlinks at fixed directories or files"
                )
            with ExitStack() as cleanup:
                with _safe_diagnostic(f"could not stage {consumer.name}"):
                    consumer_table = pa.Table.from_pylist(
                        [_consumer_row(row) for row in catalogue.records], schema=_CONSUMER_SCHEMA
                    )
                    staged_consumer = _stage(consumer_table, consumer, cleanup)
                with _safe_diagnostic(f"could not stage {reference.name}"):
                    reference_table = pa.Table.from_pylist(
                        [_reference_row(row) for row in catalogue.references],
                        schema=_REFERENCE_SCHEMA,
                    )
                    staged_reference = _stage(reference_table, reference, cleanup)
                with _safe_diagnostic(f"could not publish {consumer.name}"):
                    staged_consumer.replace(consumer)
                with _safe_diagnostic(f"could not publish {reference.name}"):
                    staged_reference.replace(reference)
        return consumer, reference


@contextmanager
def _safe_diagnostic(message: str) -> Iterator[None]:
    """Report a fixed diagnostic while preserving the underlying exception as its cause."""
    try:
        yield
    except (OSError, pa.ArrowException) as error:
        raise TssourceError(message) from error


def _validate_keys(catalogue: Catalogue) -> None:
    """Require exactly one row per key on each side and full key parity."""
    consumer = {(row.site_code, row.original_name) for row in catalogue.records}
    reference = {(row.site_code, row.original_name) for row in catalogue.references}
    if len(consumer) != len(catalogue.records) or len(reference) != len(catalogue.references):
        raise TssourceError("catalogue rows contain duplicate source and name keys")
    if consumer != reference:
        raise TssourceError("catalogue and private reference keys differ")


def _consumer_row(row: ConsumerTag) -> dict[str, object]:
    """Allow only the observed fields across the consumer boundary."""
    return {
        "site_code": row.site_code.value,
        "original_name": row.original_name,
        "descriptor": row.descriptor,
        "reported_unit": row.reported_unit,
        "data_type": row.data_type,
        "scan_class": row.scan_class.value,
        "expected_interval_seconds": row.expected_interval_seconds,
        "generator": row.generator,
    }


def _reference_row(row: ReferenceTag) -> dict[str, object]:
    """Serialize the evaluator's identity links and naming annotations."""
    return {
        "site_code": row.site_code.value,
        "original_name": row.original_name,
        "equipment_id": row.equipment_id,
        "instrument_id": row.instrument_id,
        "loop_id": row.loop_id,
        "measurement": row.measurement,
        "canonical_unit": row.canonical_unit,
        "canonical_name": row.canonical_name,
        "tier": row.tier.value,
        "violations": [variation.value for variation in row.violations],
        "holdout": row.holdout,
        "old_alias": row.old_alias,
        "replaced_at": row.replaced_at,
    }


def _stage(table: pa.Table, target: Path, cleanup: ExitStack) -> Path:
    """Write beside the destination and verify the staged schema and row count."""
    table.validate(full=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=target.parent, prefix=".catalogue-", suffix=".tmp", delete=False
    ) as file:
        staged = Path(file.name)
        cleanup.callback(staged.unlink, missing_ok=True)
        os.fchmod(file.fileno(), 0o600)
    pq.write_table(table, staged)  # type: ignore[no-untyped-call]
    with pq.ParquetFile(staged) as parquet:  # type: ignore[no-untyped-call]
        if not parquet.schema_arrow.equals(table.schema, check_metadata=True):
            raise TssourceError(f"staged {target.name} schema differs from the expected schema")
        if parquet.metadata.num_rows != table.num_rows:
            raise TssourceError(f"staged {target.name} row count differs from the expected count")
    return staged
