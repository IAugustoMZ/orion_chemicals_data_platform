"""Composition root: the only place that reads the environment and wires adapters.

Everything above it (the command line) receives ready-made objects; everything below it
receives ports. It wires the settings (card 01) and the benchmark use case with its adapters
(card 02): the only place that knows numpy, pyarrow and the file names.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from tssource.application.bench import EventSink, RunBenchmark
from tssource.application.settings import Settings
from tssource.domain.benchmark import BenchResult, Format
from tssource.infrastructure.clock import MonotonicClock
from tssource.infrastructure.numpy_source import NumpyBlockSource
from tssource.infrastructure.probe import ProcessResourceProbe
from tssource.infrastructure.sinks import JsonlGzipSink, JsonlSink, ParquetSink

_SINKS: dict[Format, tuple[str, type[JsonlGzipSink] | type[JsonlSink] | type[ParquetSink]]] = {
    Format.JSONL_GZIP: ("bench.jsonl.gz", JsonlGzipSink),
    Format.JSONL: ("bench.jsonl", JsonlSink),
    Format.PARQUET: ("bench.parquet", ParquetSink),
}


def build_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Read the settings once.

    Args:
        environ: variables to read; defaults to the process environment.

    Returns:
        The immutable settings.
    """
    return Settings.from_environment(os.environ if environ is None else environ)


def run_bench(
    seconds: int, fmt: Format, seed: int | None = None, out: Path | None = None
) -> BenchResult:
    """Run the throughput spike with real adapters and remove its scratch file afterwards.

    Args:
        seconds: wall-clock seconds to run.
        fmt: serialiser to measure.
        seed: overrides ``TSSOURCE_SEED`` when given.
        out: overrides ``TSSOURCE_OUT`` (the scratch folder) when given.

    Returns:
        The measurements. The scratch file is deleted; only ``bench.json`` (written by the
        caller) stays.
    """
    base = build_settings()
    settings = replace(
        base,
        seed=base.seed if seed is None else seed,
        output_folder=base.output_folder if out is None else out,
    )
    settings.output_folder.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="bench-", dir=settings.output_folder))
    try:
        filename, sink_class = _SINKS[fmt]
        sink: EventSink = sink_class(scratch / filename)
        use_case = RunBenchmark(
            NumpyBlockSource(settings.seed), sink, ProcessResourceProbe(), MonotonicClock()
        )
        return use_case.run(seconds=seconds, seed=settings.seed, fmt=fmt)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
