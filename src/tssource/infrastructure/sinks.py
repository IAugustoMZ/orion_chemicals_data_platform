"""The three candidate serialisers of the spike, one adapter per ``EventSink``.

Infrastructure layer. Each sink writes a whole block to one file and never changes the block, so
any sink can replace another (Liskov). A foreign payload is a programming error and is reported
in one line. The final file layout is decided later (card 15 of 001); here only speed is measured.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import IO

import pyarrow as pa
import pyarrow.parquet as pq

from tssource.domain.benchmark import Block
from tssource.domain.errors import TssourceError
from tssource.infrastructure.numpy_source import Columns


def _columns(block: Block) -> Columns:
    """Narrow the opaque payload to the numpy columns, or fail in one line."""
    if not isinstance(block.payload, Columns):
        raise TssourceError("sink received a block that was not made by the numpy source")
    return block.payload


def _jsonl(columns: Columns) -> bytes:
    """One JSON object per line: {"ts": epoch ms, "tag": id, "value": float}."""
    rows = zip(
        columns.timestamps_ms.tolist(),
        columns.tag_ids.tolist(),
        columns.values.tolist(),
        strict=True,
    )
    text = "\n".join(f'{{"ts":{t},"tag":{g},"value":{v!r}}}' for t, g, v in rows)
    return (text + "\n").encode()


class JsonlSink:
    """Plain JSON Lines."""

    def __init__(self, path: Path) -> None:
        """Open ``path`` for writing."""
        self._file: IO[bytes] = path.open("wb")

    def write(self, block: Block) -> None:
        """Append the block as lines."""
        self._file.write(_jsonl(_columns(block)))

    def close(self) -> None:
        """Close the file."""
        self._file.close()


class JsonlGzipSink:
    """JSON Lines, gzip-compressed (zlib level 6, the default most tools use)."""

    def __init__(self, path: Path) -> None:
        """Open ``path`` for writing."""
        self._file = gzip.GzipFile(path, "wb")  # noqa: SIM115 - closed in close()

    def write(self, block: Block) -> None:
        """Append the block as compressed lines."""
        self._file.write(_jsonl(_columns(block)))

    def close(self) -> None:
        """Finish the gzip stream and close the file."""
        self._file.close()


class ParquetSink:
    """Parquet, one row group per block."""

    def __init__(self, path: Path) -> None:
        """Remember the target; the writer opens on the first block (it needs the schema)."""
        self._path = path
        self._writer: pq.ParquetWriter | None = None

    def write(self, block: Block) -> None:
        """Append the block as one row group."""
        columns = _columns(block)
        table = pa.table(
            {"ts": columns.timestamps_ms, "tag": columns.tag_ids, "value": columns.values}
        )
        if self._writer is None:
            self._writer = pq.ParquetWriter(str(self._path), table.schema)  # type: ignore[no-untyped-call]
        self._writer.write_table(table)  # type: ignore[no-untyped-call]

    def close(self) -> None:
        """Write the footer and close the file."""
        if self._writer is not None:
            self._writer.close()  # type: ignore[no-untyped-call]
