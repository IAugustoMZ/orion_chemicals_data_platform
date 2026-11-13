"""The benchmark use case: one generation thread, one writer thread, a bounded queue.

Application layer. It depends only on four small ports (``EventSource``, ``EventSink``,
``ResourceProbe``, ``Clock``), so tests use fakes and the writer is swappable (ADR-0027).

How the bottleneck is named: the producer counts the times it found the queue full (the writer is
behind), the writer counts the times it found the queue empty (generation is behind). The stage
that made the *other* one wait is the limit. Counting waits, not seconds, keeps it deterministic.
"""

from __future__ import annotations

import queue
import threading
from typing import Protocol

from tssource.domain.benchmark import (
    FLOOR_EVENTS_PER_SECOND,
    BenchResult,
    Block,
    Bottleneck,
    Distribution,
    Format,
)
from tssource.domain.errors import TssourceError

_POLL_SECONDS = 0.05


class EventSource(Protocol):
    """Produces the next block of events, deterministically for a seed."""

    def next_block(self) -> Block:
        """Return the next block."""
        ...


class EventSink(Protocol):
    """Writes blocks whole into one serialisation format."""

    def write(self, block: Block) -> None:
        """Write one block."""
        ...

    def close(self) -> None:
        """Flush and release the file."""
        ...


class ResourceProbe(Protocol):
    """Reads the process cost of the run."""

    def cpu_seconds(self) -> float:
        """CPU seconds used by the process so far."""
        ...

    def peak_memory_mb(self) -> float:
        """Peak resident memory of the process in MB."""
        ...


class Clock(Protocol):
    """Wall time, injectable so tests do not wait."""

    def now(self) -> float:
        """Seconds on a monotonic scale."""
        ...


class RunBenchmark:
    """Measure how many events per second a source-to-sink pipeline sustains."""

    def __init__(
        self,
        source: EventSource,
        sink: EventSink,
        probe: ResourceProbe,
        clock: Clock,
        queue_bound: int = 8,
    ) -> None:
        """Hold the ports and the queue bound (the backpressure limit, in blocks)."""
        self._source, self._sink, self._probe, self._clock = source, sink, probe, clock
        self._bound = queue_bound

    def run(
        self, seconds: int, seed: int, fmt: Format, floor: int = FLOOR_EVENTS_PER_SECOND
    ) -> BenchResult:
        """Run for ``seconds`` of wall time and return the measurements.

        Raises:
            TssourceError: the writer failed (the message carries the cause).
        """
        pipe: queue.Queue[Block | None] = queue.Queue(maxsize=self._bound)
        stop = threading.Event()
        counts = [0] * seconds
        state = _State()
        cpu_start = self._probe.cpu_seconds()
        start = self._clock.now()
        writer = threading.Thread(
            target=self._write_loop, args=(pipe, stop, counts, start, state), name="writer"
        )
        writer.start()
        try:
            self._generate_loop(pipe, stop, start + seconds, state)
        except BaseException:
            stop.set()
            raise
        finally:
            writer.join()
            self._sink.close()
        if state.error is not None:
            raise TssourceError(f"writer failed: {state.error}") from state.error
        return BenchResult(
            seed=seed,
            fmt=fmt,
            seconds=seconds,
            events=sum(counts),
            distribution=Distribution.from_rates([float(c) for c in counts]),
            cpu_seconds=self._probe.cpu_seconds() - cpu_start,
            peak_memory_mb=self._probe.peak_memory_mb(),
            bottleneck=Bottleneck.WRITING if state.full > state.empty else Bottleneck.GENERATION,
            max_queue_depth=state.max_depth,
            queue_bound=self._bound,
            floor=floor,
        )

    def _generate_loop(
        self,
        pipe: queue.Queue[Block | None],
        stop: threading.Event,
        deadline: float,
        state: _State,
    ) -> None:
        """Producer: make blocks until the deadline, then send the end marker."""
        while self._clock.now() < deadline and not stop.is_set():
            self._put(pipe, self._source.next_block(), stop, state)
        self._put(pipe, None, stop, state)

    def _put(
        self,
        pipe: queue.Queue[Block | None],
        item: Block | None,
        stop: threading.Event,
        state: _State,
    ) -> None:
        """Put with backpressure: count a full queue once, then wait unless the writer died."""
        try:
            pipe.put_nowait(item)
        except queue.Full:
            state.full += 1
            while not stop.is_set():
                try:
                    pipe.put(item, timeout=_POLL_SECONDS)
                    break
                except queue.Full:
                    continue
        state.max_depth = max(state.max_depth, pipe.qsize())

    @staticmethod
    def _wait_for_block(pipe: queue.Queue[Block | None], stop: threading.Event) -> Block | None:
        """Wait for the next block; give up (None) if the producer failed and stopped the run."""
        while not stop.is_set():
            try:
                return pipe.get(timeout=_POLL_SECONDS)
            except queue.Empty:
                continue
        return None

    def _write_loop(
        self,
        pipe: queue.Queue[Block | None],
        stop: threading.Event,
        counts: list[int],
        start: float,
        state: _State,
    ) -> None:
        """Consumer: write every block; count it in the second in which it finished."""
        try:
            while True:
                try:
                    item = pipe.get_nowait()
                except queue.Empty:
                    state.empty += 1
                    item = self._wait_for_block(pipe, stop)
                if item is None:
                    return
                self._sink.write(item)
                bucket = int(self._clock.now() - start)
                if bucket < len(counts):
                    counts[bucket] += item.count
        except Exception as error:  # noqa: BLE001 - any writer failure must stop the producer
            state.error = error
            stop.set()


class _State:
    """Counters shared by the two threads; each field has a single writer thread."""

    def __init__(self) -> None:
        self.full = 0
        self.empty = 0
        self.max_depth = 0
        self.error: Exception | None = None
