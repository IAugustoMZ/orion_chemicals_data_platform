"""The throughput spike: distribution maths, queue bound, exit code 3 and determinism (B04-B07).

The use case is tested with fakes and a fake clock that only the fakes advance, so the runs are
fast and do not depend on how quick the machine is. Real adapters get small, direct tests.
"""

from __future__ import annotations

import gzip
import json
import threading
import time
from pathlib import Path
from typing import cast

import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from tssource.application.bench import RunBenchmark
from tssource.domain.benchmark import (
    FLOOR_EVENTS_PER_SECOND,
    BenchResult,
    Block,
    Bottleneck,
    Distribution,
    Format,
)
from tssource.domain.errors import TssourceError
from tssource.infrastructure.clock import MonotonicClock
from tssource.infrastructure.numpy_source import TAGS, TICKS_PER_BLOCK, Columns, NumpyBlockSource
from tssource.infrastructure.probe import ProcessResourceProbe
from tssource.infrastructure.sinks import JsonlGzipSink, JsonlSink, ParquetSink
from tssource.interfaces.cli import app as cli
from tssource.interfaces.cli.app import app

runner = CliRunner()


class FakeClock:
    """A clock that moves only when a fake stage says time passed."""

    def __init__(self) -> None:
        self._now = 0.0
        self._lock = threading.Lock()

    def now(self) -> float:
        """Current fake time."""
        with self._lock:
            return self._now

    def advance(self, seconds: float) -> None:
        """Let ``seconds`` of fake time pass."""
        with self._lock:
            self._now += seconds


class FakeSource:
    """Yields blocks of ``size`` events; each call costs ``cost`` fake seconds."""

    def __init__(self, clock: FakeClock, size: int = 100, cost: float = 0.0) -> None:
        self._clock, self._size, self._cost = clock, size, cost

    def next_block(self) -> Block:
        """Return the next block, spending ``cost``."""
        self._clock.advance(self._cost)
        if self._cost >= 0.01:
            time.sleep(0.002)  # a slow stage must also be slow in real time, or queues never fill
        return Block(count=self._size, payload=None)


class FakeSink:
    """Accepts blocks; each write costs ``cost`` fake seconds."""

    def __init__(self, clock: FakeClock, cost: float = 0.0) -> None:
        self._clock, self._cost = clock, cost
        self.closed = False

    def write(self, block: Block) -> None:
        """Pretend to write, spending ``cost``."""
        self._clock.advance(self._cost)
        if self._cost >= 0.01:
            time.sleep(0.002)  # see FakeSource.next_block

    def close(self) -> None:
        """Remember that the sink was closed."""
        self.closed = True


class FakeProbe:
    """Reports 1.0 CPU second at the start and 2.5 at the end."""

    def __init__(self) -> None:
        self._calls = 0

    def cpu_seconds(self) -> float:
        """First call 1.0, later calls 2.5."""
        self._calls += 1
        return 1.0 if self._calls == 1 else 2.5

    def peak_memory_mb(self) -> float:
        """A constant."""
        return 123.0


def _run(
    source_cost: float, sink_cost: float, *, bound: int = 8, seconds: int = 3
) -> tuple[BenchResult, FakeSink]:
    clock = FakeClock()
    sink = FakeSink(clock, sink_cost)
    use_case = RunBenchmark(FakeSource(clock, cost=source_cost), sink, FakeProbe(), clock, bound)
    return use_case.run(seconds=seconds, seed=1, fmt=Format.JSONL), sink


def _columns(block: Block) -> Columns:
    return cast(Columns, block.payload)


@pytest.mark.ac("PBI-003-02:AC1")
def test_distribution_maths() -> None:
    """Mean, percentiles (linear interpolation) and minimum of per-second rates."""
    distribution = Distribution.from_rates([10, 20, 30, 40, 50])
    assert distribution.mean == pytest.approx(30)
    assert distribution.p50 == pytest.approx(30)
    assert distribution.p95 == pytest.approx(48)
    assert distribution.p99 == pytest.approx(49.6)
    assert distribution.minimum == 10


@pytest.mark.ac("PBI-003-02:AC1")
def test_distribution_needs_at_least_one_second() -> None:
    """No rates means the run measured nothing: that is an error, not a zero."""
    with pytest.raises(TssourceError):
        Distribution.from_rates([])


@pytest.mark.ac("PBI-003-02:AC1")
def test_result_carries_cpu_memory_and_events_and_closes_the_sink() -> None:
    """CPU seconds are the difference over the run; the sink is always closed."""
    result, sink = _run(source_cost=0.0, sink_cost=0.001, seconds=2)
    assert result.cpu_seconds == pytest.approx(1.5)
    assert result.peak_memory_mb == 123.0
    assert result.events > 0
    assert result.floor_held is True
    assert sink.closed


@pytest.mark.ac("PBI-003-02:AC1")
def test_bench_json_has_the_contract_fields() -> None:
    """`bench.json` version 1 has exactly the names the spec promises."""
    result, _ = _run(source_cost=0.0, sink_cost=0.001, seconds=2)
    document = result.as_json()
    assert document["version"] == 1
    assert set(document) == {
        "version",
        "seed",
        "format",
        "seconds",
        "events",
        "events_per_second",
        "cpu_seconds",
        "peak_memory_mb",
        "floor",
        "floor_held",
        "bottleneck",
    }
    rates = cast(dict[str, float], document["events_per_second"])
    assert set(rates) == {"mean", "p50", "p95", "p99", "min"}


@pytest.mark.ac("PBI-003-02:AC2")
def test_queue_depth_never_exceeds_its_bound() -> None:
    """A slow writer fills the queue to its bound and never past it."""
    result, _ = _run(source_cost=0.0, sink_cost=0.1, bound=3)
    assert result.queue_bound == 3
    assert 0 < result.max_queue_depth <= 3


@pytest.mark.ac("PBI-003-02:AC3")
def test_slow_writer_is_named_as_the_bottleneck() -> None:
    """The producer keeps meeting a full queue: writing is the limit, and the floor is missed."""
    result, _ = _run(source_cost=0.0, sink_cost=0.1)
    assert result.bottleneck is Bottleneck.WRITING
    assert result.floor_held is False
    assert result.distribution.mean < FLOOR_EVENTS_PER_SECOND


@pytest.mark.ac("PBI-003-02:AC3")
def test_slow_generation_is_named_as_the_bottleneck() -> None:
    """The writer keeps finding an empty queue: generation is the limit."""
    result, _ = _run(source_cost=0.1, sink_cost=0.0)
    assert result.bottleneck is Bottleneck.GENERATION
    assert result.floor_held is False


@pytest.mark.ac("PBI-003-02:AC3")
def test_a_failing_sink_surfaces_as_a_handled_error() -> None:
    """A writer that raises must stop the producer and reach the caller, not hang."""

    class Broken(FakeSink):
        def write(self, block: Block) -> None:
            raise OSError("disk full")

    clock = FakeClock()
    use_case = RunBenchmark(FakeSource(clock), Broken(clock), FakeProbe(), clock, 2)
    with pytest.raises(TssourceError, match="disk full"):
        use_case.run(seconds=2, seed=1, fmt=Format.JSONL)


@pytest.mark.ac("PBI-003-02:AC3")
def test_cli_exits_three_and_names_the_stage_below_the_floor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Below the floor `bench` still writes `bench.json`, exits 3 and prints the stage."""
    result, _ = _run(source_cost=0.0, sink_cost=0.1)
    monkeypatch.setattr(cli, "run_bench", lambda **_: result)
    outcome = runner.invoke(app, ["bench", "--seconds", "3", "--out", str(tmp_path)])
    assert outcome.exit_code == 3
    assert "writing" in outcome.output
    assert (tmp_path / "bench.json").exists()


@pytest.mark.ac("PBI-003-02:AC1")
def test_cli_writes_bench_json_and_exits_zero_when_the_floor_holds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Above the floor `bench` writes `bench.json` and exits 0."""
    result, _ = _run(source_cost=0.0, sink_cost=0.001, seconds=2)
    monkeypatch.setattr(cli, "run_bench", lambda **_: result)
    outcome = runner.invoke(app, ["bench", "--out", str(tmp_path)])
    assert outcome.exit_code == 0
    assert json.loads((tmp_path / "bench.json").read_text())["floor_held"] is True


@pytest.mark.ac("PBI-003-02:AC1")
@pytest.mark.parametrize("fmt", ["jsonl", "jsonl-gzip", "parquet"])
def test_cli_real_run_writes_bench_json_and_removes_scratch(tmp_path: Path, fmt: str) -> None:
    """One real second with real adapters: exit 0 or 3 (machine speed), a document, no scratch."""
    outcome = runner.invoke(
        app, ["bench", "--seconds", "1", "--format", fmt, "--out", str(tmp_path)]
    )
    assert outcome.exit_code in (0, 3)
    assert json.loads((tmp_path / "bench.json").read_text())["format"] == fmt
    assert [p.name for p in tmp_path.iterdir()] == ["bench.json"]


@pytest.mark.ac("PBI-003-02:AC4")
def test_same_seed_gives_the_same_events() -> None:
    """Two sources with one seed give equal blocks; another seed gives different ones."""
    first, second, other = NumpyBlockSource(7), NumpyBlockSource(7), NumpyBlockSource(8)
    for _ in range(3):
        a, b, c = first.next_block(), second.next_block(), other.next_block()
        assert a.count == TICKS_PER_BLOCK * TAGS
        assert _columns(a).values.tolist() == _columns(b).values.tolist()
        assert _columns(a).timestamps_ms.tolist() == _columns(b).timestamps_ms.tolist()
        assert _columns(a).values.tolist() != _columns(c).values.tolist()


@pytest.mark.ac("PBI-003-02:AC4")
def test_the_clock_of_events_continues_across_blocks() -> None:
    """The second block starts after the first ended (one continuous scan)."""
    source = NumpyBlockSource(3)
    first, second = source.next_block(), source.next_block()
    assert _columns(second).timestamps_ms[0] > _columns(first).timestamps_ms[-1]


@pytest.mark.ac("PBI-003-02:AC4")
def test_same_seed_gives_identical_files(tmp_path: Path) -> None:
    """The bytes on disk are equal for one seed, so runs can be compared."""
    for name in ("a", "b"):
        sink = JsonlSink(tmp_path / f"{name}.jsonl")
        source = NumpyBlockSource(11)
        for _ in range(2):
            sink.write(source.next_block())
        sink.close()
    assert (tmp_path / "a.jsonl").read_bytes() == (tmp_path / "b.jsonl").read_bytes()


@pytest.mark.ac("PBI-003-02:AC1")
def test_each_sink_writes_every_event(tmp_path: Path) -> None:
    """All three serialisers write the whole block and produce a readable file."""
    block = NumpyBlockSource(5).next_block()
    for sink in (
        JsonlGzipSink(tmp_path / "x.jsonl.gz"),
        JsonlSink(tmp_path / "x.jsonl"),
        ParquetSink(tmp_path / "x.parquet"),
    ):
        sink.write(block)
        sink.close()
    with gzip.open(tmp_path / "x.jsonl.gz", "rt") as handle:
        assert sum(1 for _ in handle) == block.count
    assert len((tmp_path / "x.jsonl").read_text().splitlines()) == block.count
    assert pq.read_table(tmp_path / "x.parquet").num_rows == block.count


def test_sink_rejects_a_foreign_block(tmp_path: Path) -> None:
    """A block that is not the numpy columns is a programming error, said in one line."""
    with pytest.raises(TssourceError):
        JsonlSink(tmp_path / "y.jsonl").write(Block(count=1, payload="nope"))


def test_probe_and_clock_report_sane_values() -> None:
    """CPU time grows with work, memory is not negative, the clock never goes back."""
    probe, clock = ProcessResourceProbe(), MonotonicClock()
    before, t0 = probe.cpu_seconds(), clock.now()
    sum(i * i for i in range(200_000))
    assert probe.cpu_seconds() >= before
    assert probe.peak_memory_mb() >= 0.0
    assert clock.now() >= t0


@pytest.mark.ac("PBI-003-02:AC3")
def test_seconds_has_an_upper_bound(tmp_path: Path) -> None:
    """`--seconds` above one hour is a usage error (exit 2), so a typo cannot fill the disk."""
    outcome = runner.invoke(app, ["bench", "--seconds", "3601", "--out", str(tmp_path)])
    assert outcome.exit_code == 2
    assert not (tmp_path / "bench.json").exists()
