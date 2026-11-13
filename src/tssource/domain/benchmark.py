"""Pure value objects of the throughput spike: blocks, distribution and result.

Domain layer: no numpy, no pyarrow, no I/O. ``Distribution`` turns a list of per-second rates
into the numbers RT29 asks for, so a slow second cannot hide behind a fast average (ADR-0027).
``BenchResult`` is what ``tssource bench`` reports and what ``bench.json`` (version 1) holds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from tssource.domain.errors import TssourceError

FLOOR_EVENTS_PER_SECOND = 25_000
"""The sustained rate the generator must reach in backfill (RT29)."""


class Format(StrEnum):
    """The candidate serialisers measured by the spike."""

    JSONL_GZIP = "jsonl-gzip"
    JSONL = "jsonl"
    PARQUET = "parquet"


class Bottleneck(StrEnum):
    """The stage that limited the run."""

    GENERATION = "generation"
    WRITING = "writing"


@dataclass(frozen=True)
class Block:
    """A batch of events handed from the source to the sink.

    Attributes:
        count: how many events the block holds (what the rate counts).
        payload: the data itself; only the adapters on both ends know its shape.
    """

    count: int
    payload: object


@dataclass(frozen=True)
class Distribution:
    """Mean, percentiles and minimum of the events written in each second of wall time."""

    mean: float
    p50: float
    p95: float
    p99: float
    minimum: float

    @classmethod
    def from_rates(cls, rates: list[float]) -> Distribution:
        """Summarise per-second rates; percentiles use linear interpolation.

        Raises:
            TssourceError: ``rates`` is empty, because nothing was measured.
        """
        if not rates:
            raise TssourceError("the run measured no full second; raise --seconds")
        ordered = sorted(rates)
        return cls(
            mean=sum(ordered) / len(ordered),
            p50=_percentile(ordered, 50),
            p95=_percentile(ordered, 95),
            p99=_percentile(ordered, 99),
            minimum=ordered[0],
        )


def _percentile(ordered: list[float], percent: float) -> float:
    """Linear-interpolated percentile of an already sorted, non-empty list."""
    position = (len(ordered) - 1) * percent / 100
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


@dataclass(frozen=True)
class BenchResult:
    """Everything one benchmark run measured."""

    seed: int
    fmt: Format
    seconds: int
    events: int
    distribution: Distribution
    cpu_seconds: float
    peak_memory_mb: float
    bottleneck: Bottleneck
    max_queue_depth: int
    queue_bound: int
    floor: int = FLOOR_EVENTS_PER_SECOND

    @property
    def floor_held(self) -> bool:
        """True when the MEAN rate reached the floor (minimum and p99 are only reported)."""
        return self.distribution.mean >= self.floor

    def as_json(self) -> dict[str, object]:
        """The ``bench.json`` document, version 1 (names are stable, additions only)."""
        d = self.distribution
        return {
            "version": 1,
            "seed": self.seed,
            "format": self.fmt.value,
            "seconds": self.seconds,
            "events": self.events,
            "events_per_second": {
                "mean": d.mean,
                "p50": d.p50,
                "p95": d.p95,
                "p99": d.p99,
                "min": d.minimum,
            },
            "cpu_seconds": self.cpu_seconds,
            "peak_memory_mb": self.peak_memory_mb,
            "floor": self.floor,
            "floor_held": self.floor_held,
            "bottleneck": self.bottleneck.value,
        }
