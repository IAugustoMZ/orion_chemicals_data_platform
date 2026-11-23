"""Composition root: the only place that reads the environment and wires adapters.

The command line receives ready-made objects. Application use cases receive ports.
This module supplies the benchmark, time core, plant and catalogue adapters.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from pathlib import Path

from tssource.application.bench import EventSink, RunBenchmark
from tssource.application.catalogue import BuildCatalogue
from tssource.application.plant import BuildPlant
from tssource.application.settings import Settings
from tssource.application.time_table import ResolveTimeTable
from tssource.application.timestamp_codec import TimestampCodec
from tssource.domain.benchmark import BenchResult, Format
from tssource.domain.naming.catalogue_builder import CatalogueBuilder
from tssource.domain.plant.builder import PlantBuilder
from tssource.domain.time.resolution import LocalResolution
from tssource.domain.time.site_zone import SITE_ZONES, SiteCode
from tssource.infrastructure.catalogue_parquet import CatalogueParquetWriter
from tssource.infrastructure.clock import MonotonicClock
from tssource.infrastructure.naming_draws import SeededDrawSource
from tssource.infrastructure.numpy_source import NumpyBlockSource
from tssource.infrastructure.plant_json import PlantJsonWriter
from tssource.infrastructure.probe import ProcessResourceProbe
from tssource.infrastructure.sinks import JsonlGzipSink, JsonlSink, ParquetSink
from tssource.infrastructure.zoneinfo_resolver import ZoneInfoResolver

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


def resolve_time_table(site_code: str, requested_date: date) -> tuple[LocalResolution, ...]:
    """Resolve one declared site's 24 local clock hours through the application use case.

    Raises:
        ValueError: ``site_code`` is not one of the declared fictional sites.
    """
    try:
        site = SITE_ZONES[SiteCode(site_code)]
    except ValueError as error:
        allowed = ", ".join(code.value for code in SiteCode)
        raise ValueError(f"unknown site '{site_code}'; choose one of: {allowed}") from error
    return ResolveTimeTable(ZoneInfoResolver()).resolve(site, requested_date)


def build_timestamp_codec() -> TimestampCodec:
    """Wire the timestamp codec with the declared-site resolver used by the CLI."""
    return TimestampCodec(ZoneInfoResolver())


def build_plant_use_case() -> BuildPlant:
    """Wire the deterministic plant builder to the private JSON writer."""
    return BuildPlant(PlantBuilder(), PlantJsonWriter())


def build_catalogue_builder(seed: int) -> CatalogueBuilder:
    """Wire the in-memory catalogue builder to deterministic draw streams."""
    return CatalogueBuilder(SeededDrawSource(seed))


def build_catalogue_use_case(seed: int) -> BuildCatalogue:
    """Wire both deterministic generators with one seed and a Parquet pair writer."""
    return BuildCatalogue(
        seed, PlantBuilder(), build_catalogue_builder(seed), CatalogueParquetWriter()
    )
