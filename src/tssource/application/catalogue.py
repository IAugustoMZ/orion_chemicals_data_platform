"""Build one catalogue snapshot and publish its two projections through a port."""

from pathlib import Path
from typing import Protocol

from tssource.domain.naming.catalogue_builder import CatalogueBuilder
from tssource.domain.naming.model import Catalogue
from tssource.domain.plant.builder import PlantBuilder


class CatalogueWriter(Protocol):
    """Publish the consumer catalogue and its matching private reference."""

    def write(self, catalogue: Catalogue, output_folder: Path) -> tuple[Path, Path]:
        """Return consumer then reference paths after successful publication."""
        ...


class BuildCatalogue:
    """Coordinate same-seed plant generation, naming and publication."""

    def __init__(
        self,
        seed: int,
        plant_builder: PlantBuilder,
        catalogue_builder: CatalogueBuilder,
        writer: CatalogueWriter,
    ) -> None:
        """Receive the plant builder, seeded catalogue builder and output adapter."""
        self._seed = seed
        self._plant_builder = plant_builder
        self._catalogue_builder = catalogue_builder
        self._writer = writer

    def execute(self, output_folder: Path) -> tuple[Path, Path]:
        """Build the plant in memory and publish one pair from its tag snapshot."""
        catalogue = self._catalogue_builder.build(self._plant_builder.build(self._seed))
        return self._writer.write(catalogue, output_folder)
