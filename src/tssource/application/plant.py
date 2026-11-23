"""Coordinate deterministic plant construction and private publication."""

from pathlib import Path
from typing import Protocol

from tssource.domain.plant.builder import PlantBuilder
from tssource.domain.plant.model import Plant


class PlantWriter(Protocol):
    """Publish a plant to the operator's output directory."""

    def write(self, plant: Plant, output_folder: Path) -> Path:
        """Return the fixed output path after success or raise a handled write error."""
        ...


class BuildPlant:
    """Give the CLI a single build operation independent of storage format."""

    def __init__(self, builder: PlantBuilder, writer: PlantWriter) -> None:
        """Receive the pure generator and the writer from the composition root."""
        self._builder = builder
        self._writer = writer

    def execute(self, seed: int, output_folder: Path) -> Path:
        """Build with the given seed and return a path after the writer commits it."""
        return self._writer.write(self._builder.build(seed), output_folder)
